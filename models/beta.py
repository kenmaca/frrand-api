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
        ''' (BetaKey, User) -> BetaKey
        Sets this BetaKey as used by the User.
        '''

        self.push('usedBy', user.getId())
        return self

    def isUsed(self):
        ''' (BetaKey) -> bool
        Determines if this BetaKey has been used or not.
        '''

        return len(self.get('usedBy')) >= self.get('limit')

    def getSupplement(self):
        ''' (BetaKey) -> int
        Gets the point value supplement to provision to the newly created account.
        '''

        return self.get('pointSupplement')
