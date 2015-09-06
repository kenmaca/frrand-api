from models.orm import MongoORM
from models.requestInvites import Invite

class PublicInvite(MongoORM):
    ''' A representation of an PublicInvite for a Request in Frrand.
    '''

    collection = 'publicRequestInvites'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> PublicInvite
        Creates an PublicInvite directly from db with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(db, objectId, PublicInvite)

    def embedView(self):
        ''' (PublicInvite) -> dict
        Embeds the parent Request as well as any other inaccessable documents.
        '''

        # use invite's embedView as they share similarities
        return Invite.embedView(self)