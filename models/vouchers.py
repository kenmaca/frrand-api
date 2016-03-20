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

        if not self.isUsed() and self.isEligible(user):
            self.push('usedBy', user.getId())
            user.set('activated', True).increment('points', self.getSupplement()).commit()
            self.getGroup() and self.getGroup().join(user)
        return self

    def isUsed(self):
        ''' (Voucher) -> bool
        Determines if this Voucher has been depleted yet.
        '''

        return len(self.get('usedBy')) >= self.get('limit')

    def isEligible(self, user):
        ''' (Voucher, User) -> bool
        Determines if user is eligible to use this Voucher.
        '''

        return not (user.getId() in self.get('usedBy'))

    def getSupplement(self):
        ''' (Voucher) -> int
        Gets the point value supplement to provision to the newly created account.
        '''

        return self.get('pointSupplement')

    def getGroup(self):
        ''' (Voucher) -> Group
        Gets the Group that this Voucher will attach to an User when used.
        '''

        if self.exists('groupAttach') and self.get('groupAttach'):
            import models.groups
            try:
                return models.groups.fromObjectId(self.db, self.get('groupAttach'))
            except KeyError:
                pass
