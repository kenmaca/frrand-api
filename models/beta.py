import models.orm as orm
from datetime import datetime

class BetaKey(orm.MongoORM):
    ''' A representation of an BetaKey in Frrand.
    '''

    collection = 'beta'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> BetaKey
        Creates a BetaKey directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, BetaKey)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> BetaKey
        Finds a single BetaKey given query.
        '''

        return orm.MongoORM.findOne(db, BetaKey, **query)

    def use(self, user):
        ''' (BetaKey, User) -> NoneType
        Sets this BetaKey as used by the User.
        '''

        self.set('usedBy', user.getId())
        self.set('usedOn', datetime.utcnow())

    def isUsed(self):
        ''' (BetaKey) -> bool
        Determines if this BetaKey has been used or not.
        '''

        return self.exists('usedBy')