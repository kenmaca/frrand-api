from models.orm import MongoORM
from datetime import datetime, timedelta
from pytz import UTC
from models.requests import Request
from models.addresses import Address
from models.users import User

class Invite(MongoORM):
    ''' A representation of an Invite for a Request in Frrand.
    '''

    collection = 'requestInvites'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Invite
        Creates an Invite directly from db with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(db, objectId, Invite)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Invite
        Finds a single Invite given query.
        '''

        return MongoORM.findOne(db, Invite, **query)

    def embedView(self):
        ''' (Invite) -> dict
        Embeds the parent Request as well as any other inaccessable documents.
        '''

        embed = self.view()
        embed['requestId'] = Request.fromObjectId(
            self.db,
            self.get('requestId')
        ).view()
        embed['requestId']['destination'] = Address.fromObjectId(
            self.db,
            embed['requestId']['destination']
        ).view()
        embed['from'] = User.fromObjectId(
            self.db,
            self.get('from')
        ).get('username')

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

        # alert owner
        (User.fromObjectId(self.db, self.get('from'))
            .message('requestInviteAccepted', self.getId())
        )