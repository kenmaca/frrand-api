import models.orm as orm
from datetime import datetime, timedelta
from pytz import UTC
import messages.requestInvites

class Invite(orm.MongoORM):
    ''' A representation of an Invite for a Request in Frrand.
    '''

    collection = 'requestInvites'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Invite
        Creates an Invite directly from db with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Invite)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Invite
        Finds a single Invite given query.
        '''

        return orm.MongoORM.findOne(db, Invite, **query)

    def embedView(self):
        ''' (Invite) -> dict
        Embeds the parent Request as well as any other inaccessable documents.
        '''

        import models.addresses as addresses

        embed = self.view()
        embed['requestId'] = self.getRequest().view()
        embed['requestId']['destination'] = addresses.Address.fromObjectId(
            self.db,
            embed['requestId']['destination']
        ).view()

        return embed

    def isExpired(self):
        ''' (Invite) -> bool
        Determines if the given requestInvite should be pruned.
        '''

        return (
            not self.get('attached')
            and (
                self.get('requestExpiry')
                < datetime.utcnow().replace(tzinfo=UTC)
            )
        )

    def addExpiry(self, minutes):
        ''' (Invite, int) -> Invite
        Adds an expiry timer of minutes minutes to this Invite.
        '''

        self.set(
            'requestExpiry',
            datetime.utcnow() + timedelta(minutes=minutes)
        )
        return self

    def accept(self):
        ''' (Invite) -> Invite
        Accepts this Invite.
        '''

        self.set('accepted', True)
        self.getRequest().getOwner().message(
            *messages.requestInvites.accepted(self.getId())
        )
        return self

    def attach(self):
        ''' (Invite) -> Invite
        Attaches this Invite.
        '''

        self.set('attached', True)
        self.getOwner().message(
            *messages.requestInvites.attached(self.getId())
        )
        return self

    def complete(self):
        ''' (Invite) -> Invite
        Marks this Invite as completed.
        '''

        self.set('complete', True)
        self.getOwner().message(
            *messages.requestInvites.completed(self.getId())
        )
        return self

    def isAccepted(self):
        ''' (Invite) -> bool
        Determines whether or not this Invite is accepted.
        '''

        return self.get('accepted')

    def isAttached(self):
        ''' (Invite) -> bool
        Determines whether or not this Invite is attached.
        '''

        return self.get('attached')

    def isComplete(self):
        ''' (Invite) -> bool
        Determines whether or not this Invite is complete.
        '''

        return self.get('complete')

    def getRequest(self):
        ''' (Invite) -> models.requests.Request
        Gets the parent Request for this Invite.
        '''

        import models.requests as requests
        return requests.Request.fromObjectId(
            self.db,
            self.get('requestId')
        )

    def getOwner(self):
        ''' (Invite) -> models.users.User
        Gets the owner of this Invite.
        '''

        import models.users as users
        return users.User.fromObjectId(
            self.db,
            self.get('createdBy')
        )

    def feedbackSubmitted(self):
        ''' (Invite) -> bool
        Determines if feedback has been submitted for this Invite yet.
        '''

        return self.exists('rating') and bool(self.get('rating'))

    def getFeedback(self):
        ''' (Request) -> Feedback
        Gets the Feedback, if any, left for the requester.
        '''

        if self.feedbackSubmitted():
            import models.feedback as feedback
            return feedback.Feedback.findOne(
                self.db,
                **{
                    'requestInviteId': self.getId(),
                    'for': self.getRequest().getOwner().getId()
                }
            )
