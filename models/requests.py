import models.orm as orm
from datetime import datetime

class Request(orm.MongoORM):
    ''' A representation of a Request in Frrand.
    '''

    collection = 'requests'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Request
        Creates a Request directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Request)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Request
        Finds a single Request given query.
        '''

        return orm.MongoORM.findOne(db, Request, **query)

    def matchCandidates(self):
        ''' (Request) -> Request
        Finds suitable candidates to offer requestInvites to based on their
        travel region and current location.
        '''

        # first, build the request's routes
        routes = []
        import models.addresses as addresses
        destination = addresses.Address.fromObjectId(
            self.db,
            self.get('destination')
        )
        
        for place in self.get('places'):
            routes += [{
                'type': 'LineString',
                'coordinates': [
                    place['location']['coordinates'],
                    destination.get('location')['coordinates']
                ]
            }]

        # then convert routes to a $geoIntersects with $or query
        intersects = [
            {
                'region': {
                    '$geoIntersects': {
                        '$geometry': route
                    }
                }
            }
            for route in routes
        ]

        # and then the full query (sorted by near the first place)
        # TODO: support multiple places, but this is a limitation of
        # MongoDB's $or operator
        query = {
            '$or': intersects,
            'location': {
                '$near': {
                    '$geometry': self.get('places')[0]['location'],

                # TODO: add maxDistance.. but during development, don't
                # restrict to allow more candidates
                }
            },
            'current': True,

            # TODO: the cut off between hours will exclude those that haven't
            # reported this hour yet.. (which depends on the clients reporting
            # schedule; example: 15 minute reporting cycle will result in up to
            # first 15 minutes not being considered)

            # will definately cause less available deliveries during the start
            # of a hour

            # actually: we can just omit the hour, as long as the current
            # attribute is reliable
            #'hour': 
            'dayOfWeek': datetime.utcnow().isoweekday()
        }

        locationOfCandidates = self.db['locations'].find(query)

        # now, filter out those candidates that aren't active
        import models.users as users
        for location in locationOfCandidates:
            candidate = users.User.fromObjectId(
                self.db,
                location['createdBy']
            )

            # prevent invites being sent out to the owner
            if (
                candidate.get('active')
                and candidate.getId() != self.get('createdBy')
            ):
                try:
                    self.addCandidate(candidate.getId())
                except ValueError:
                    pass

        return self

    def matchAllCandidates(self):
        ''' (Request) -> Request
        For development use: matches everyone as a candidate.
        '''

        import models.users as users
        for user in self.db['users'].find({}):
            user = users.User(self.db, users.User.collection, **user)
            if user.isActive():
                try:
                    self.addCandidate(user.getId())
                except ValueError:
                    pass

        return self

    def matchOwnerAsCandidate(self):
        ''' (Request) -> Request
        For development use: matches only the owner as a candidate.
        '''

        import models.users as users
        user = users.User.fromObjectId(self.db, self.get('createdBy'))
        if user.isActive():
            try:
                self.addCandidate(user.getId())
            except ValueError:
                pass

        return self

    def embedView(self):
        ''' (Request) -> dict
        Embeds requestInvites to its parent request for display.
        '''

        # build a copy of this Request to embed data into
        embed = self.view()

        # embed inviteIds
        embed['inviteIds'] = [invite.view() for invite in self.getInvites()]
        
        return embed

    def getInvites(self):
        ''' (Request) -> list of models.requestInvites.Invite
        Gets a list of all the invites that belong to this Request.
        '''

        invites = []
        import models.requestInvites as requestInvites
        for inviteId in self.get('inviteIds'):
            try:
                invites.append(
                    requestInvites.Invite.fromObjectId(
                        self.db,
                        inviteId
                    )
                )
            except KeyError:

                # invite didn't exist for some reason, so remove it here
                self.listRemove('inviteIds', inviteId)

        return invites

    def pruneExpiredInvites(self):
        ''' (Request) -> Request
        Removes all expired invites.
        '''

        [
            self.removeInvite(invite)
            for invite in self.getInvites()
            if invite.isExpired()
        ]
        return self

    def addInvite(self, invite):
        ''' (Request, models.requestInvites.Invite) -> Request
        Adds the Invite to this Request.
        '''

        self.push('inviteIds', invite.getId())
        return self

    def removeInvite(self, invite):
        ''' (Request, models.requestInvites.Invite) -> Request
        Removes the Invite from this Request.
        '''

        try:
            self.listRemove('inviteIds', invite.getId())            
            invite.remove()
        except ValueError:
            pass

        return self

    def attachInvite(self, invite):
        ''' (Request, models.requestInvites.Invite) -> Request
        Attaches the selected invite to this Request.
        '''

        # make sure that the invite is associated with this Request
        if (
            invite.getId() in self.get('inviteIds')
            and invite.get('requestId') == self.getId()

            # ensure that invite has been accepted before attaching
            and invite.get('accepted')
        ):

            # attach
            self.set('attachedInviteId', invite.getId())
            invite.attach()

            # remove all other invites and candidates
            self.set('candidates', [])
            import models.requestInvites as requestInvites
            [
                self.removeInvite(
                    requestInvites.Invite.fromObjectId(
                        self.db,
                        otherInvite
                    )
                )
                for otherInvite in self.get('inviteIds')
                if otherInvite != invite.getId()
            ]

            # remove PublicInvite if it exists
            if self.get('publicRequestInviteId'):
                import models.publicRequestInvites as publicInvites
                publicInvites.PublicInvite.fromObjectId(
                    self.db,
                    self.get('publicRequestInviteId')
                ).remove()

                self.set('publicRequestInviteId', None)

        else:
            raise ValueError('Cannot attach Invite to this Request')

        return self

    def isComplete(self):
        ''' (Request) -> bool
        Determines whether or not this Request is complete.
        '''

        return self.get('complete') or self.isMutuallyCancelled()

    def complete(self):
        ''' (Request) -> Request
        Marks this Request as completed.
        '''

        self.set('complete', True)
        self.getAttached().complete().commit()

        # transfer points from requester to invitee and update totals
        (self.getOwner()
            .spendPoints(self.getPoints())
            .increment('requestsRecieved')
            .commit()
        )
        (self.getAttached().getOwner()
            .awardPoints(self.getPoints())
            .increment('requestsDelivered')
            .commit()
        )

        return self

    def addCandidate(self, userId):
        ''' (Request, ObjectId) -> Request
        Adds the userId to this Request's candidates list.
        '''

        # prevent adding users that already have an Invite or
        # already in candidates list
        if (
            (
                userId
                in [invite.getOwner().getId() for invite in self.getInvites()]
            ) or (
                userId in self.get('candidates')
            )
        ):
            raise ValueError('Candidate already exists or has an invite')

        # otherwise, good to go            
        self.push('candidates', userId)
        return self

    def isAttached(self):
        ''' (Request) -> bool
        Determines whether or not this Request has been attached.
        '''

        try:
            return bool(self.getAttached())
        except ValueError:
            return False

    def isPublic(self):
        ''' (Request) -> bool
        Determines whether or not this Request is public.
        '''

        try:
            return bool(self.getPublic())
        except ValueError:
            return False

    def feedbackSubmitted(self):
        ''' (Request) -> bool
        Determines if feedback has been submitted for this Request yet.
        '''

        return self.exists('rating') and bool(self.get('rating'))

    def getPublic(self):
        ''' (Request) -> models.publicRequestInvites.PublicInvite
        Gets the the publicRequestInvite for this Request.
        '''

        if self.get('publicRequestInviteId'):
            import models.publicRequestInvites as publicRequestInvites
            return publicRequestInvites.PublicInvite.fromObjectId(
                self.db,
                self.get('publicRequestInviteId')
            )

    def getAttached(self):
        ''' (Request) -> models.requestInvites.Invite
        Gets the currently attached requestInvite for this Request.
        '''

        if self.get('attachedInviteId'):
            import models.requestInvites as requestInvites
            return requestInvites.Invite.fromObjectId(
                self.db,
                self.get('attachedInviteId')
            )

    def getOwner(self):
        ''' (Request) -> models.users.User
        Gets the owner of this Request.
        '''

        import models.users as users
        return users.User.fromObjectId(
            self.db,
            self.get('createdBy')
        )

    def getDestination(self):
        ''' (Request) -> models.addresses.Address
        Gets the destination for this Request.
        '''

        import models.addresses as addresses
        return addresses.Address.fromObjectId(
            self.db,
            self.get('destination')
        )

    def getPoints(self):
        ''' (Request) -> int
        Gets the number of points this Request awards on completion.
        '''

        return self.get('points')

    def getFeedback(self):
        ''' (Request) -> Feedback
        Gets the Feedback, if any, left for the deliverer.
        '''

        if self.feedbackSubmitted():
            import models.feedback as feedback
            return feedback.Feedback.findOne(
                self.db,
                **{
                    'requestId': self.getId(),
                    'for': self.getAttached().getOwner().getId()
                }
            )

    def getComments(self):
        ''' (Request) -> list of Comment
        Gets all Comments for this Request.
        '''

        import models.comments as comments
        return [
            comments.Comment(
                self.db,
                comments.Comment.collection,
                **comment
            ) for comment in self.db['comments'].find({
                'requestId': self.getId()
            })
        ]

    def requestCancellation(self):
        ''' (Request) -> Request
        Attempts to cancel this Request (by notifying all participants via
        GCM). Purges all Invites, Candidates, PublicInvites, and prevents
        any PublicInvites from being created.
        '''

        # don't allow mutually cancelled to be cancelled again
        if not self.get('isMutuallyCancelled'):

            # final cancellation stage, perform cancelling tasks
            if self.isMutuallyCancelled():

                # release points back to requester
                self.getOwner().spendPoints(
                    self.getPoints()
                ).awardPoints(
                    self.getPoints()
                ).commit()

                # remove public listing if present
                if self.isPublic():
                    self.getPublic().remove()

                # remove invites if not attached
                if not self.isAttached():
                    [self.removeInvite(invite) for invite in self.getInvites()]

                # notify all parties
                self.getOwner().message('requestMutuallyCancelled', self.getId())
                if self.isAttached():
                    self.getAttached().getOwner().message(
                        'inviteMutuallyCancelled',
                        self.getAttached().getId()
                    )

                # and public/invites arent generated because cancelled is like complete
                self.set('isMutuallyCancelled', True)

            # or prepare the cancellation process, if requester initiated
            elif self.exists('cancel') and self.get('cancel'):
                self.getAttached().getOwner().message(
                    'promptInviteCancellation',
                    self.getAttached().getId()
                )

            # if invitee is requesting a cancellation
            elif self.getAttached().get('cancel'):
                self.getOwner().message('promptRequestCancellation', self.getId())                    

        return self

    def isMutuallyCancelled(self):
        ''' (Request) -> bool
        Determines if this Request is mutually cancellable if there is
        a confirmed Invite attached to this Request.
        '''

        if self.isAttached():
            return self.exists('cancel') and self.get('cancel') and self.getAttached().exists('cancel') and self.getAttached().get('cancel')
        else:
            return self.exists('cancel') and self.get('cancel')
