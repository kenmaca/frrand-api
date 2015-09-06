from datetime import datetime
from models.orm import MongoORM
from models.requestInvites import Invite
from models.users import User
from models.addresses import Address

class Request(MongoORM):
    ''' A representation of a Request in Frrand.
    '''

    collection = 'requests'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Request
        Creates a Request directly from database with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(db, objectId, Request)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Request
        Finds a single Request given query.
        '''

        return MongoORM.findOne(db, Request, **query)

    def matchCandidates(self):
        ''' (Request) -> Request
        Finds suitable candidates to offer requestInvites to based on their
        travel region and current location.
        '''

        # first, build the request's routes
        routes = []
        destination = Address.fromObjectId(
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
        for location in locationOfCandidates:
            candidate = User.fromObjectId(
                self.db,
                location['createdBy']
            )

            # prevent invites being sent out to the owner
            if (
                candidate.get('active')
                and candidate.getId() != self.get('createdBy')
            ):
                self.push('candidates', candidate['_id'])

        return self

    def matchAllCandidates(self):
    ''' (Request) -> Request
    For development use: matches everyone as a candidate.
    '''

        users = self.db['users'].find({})
        for user in users:
            user = User(self.db, User.collection, **user)
            if user.isActive():
                self.push('candidates', user.getId())

        # now remove duplicates
        self.set('candidates', list(set(self.get('candidates'))))

        return self

    def embedView(self):
        ''' (Request) -> dict
        Embeds requestInvites to its parent request for display.
        '''

        # build a copy of this Request to embed data into
        embed = self.view()

        # embed inviteIds
        embed['inviteIds'] = [
            Invite(self.db, inviteId).view()
            for inviteId in self.get('inviteIds')
        ]

        return embed

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

        inviteIds = self.get('inviteIds')
        try:
            inviteIds.remove(invite.getId())
            invite.remove()
        except ValueError:
            pass

        return self