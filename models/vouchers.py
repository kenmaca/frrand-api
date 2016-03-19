import models.orm as orm
from datetime import datetime

class Voucher(orm.MongoORM):
    ''' A representation of an Voucher in Frrand.
    '''

    collection = 'vouchers'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Voucher
        Creates a Voucher directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Voucher)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Voucher
        Finds a single Voucher given query.
        '''

        return orm.MongoORM.findOne(db, Voucher, **query)

    def use(self, user):
        ''' (Voucher, User) -> Voucher
        Sets this Voucher as used by the User.
        '''

        self.push('usedBy', user.getId())
        return self

    def isUsed(self):
        ''' (Voucher) -> bool
        Determines if this Voucher has been depleted yet.
        '''

        return len(self.get('usedBy')) >= self.get('limit')

    def getSupplement(self):
        ''' (Voucher) -> int
        Gets the point value supplement to provision to the newly created account.
        '''

        return self.get('pointSupplement')

    def getGroup(self):
        ''' (Voucher) -> Group
        Gets the Group that this Voucher will attach to an User when used.
        '''

        pass
