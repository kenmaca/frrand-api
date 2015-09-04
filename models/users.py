from models.orm import MongoORM
from models.addresses import Address

class User(MongoORM):
    ''' A representation of an User in Frrand.
    '''

    collection = 'users'

    def __init__(self, db, **fields):
        ''' (User, pymongo.database.Database) -> User
        Instantiates a new User.
        '''

        MongoORM.__init__(self, db, User.collection, **fields)

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> User
        Creates a User directly from database with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(db, objectId, User)

    def selfOwn(self):
        ''' (User) -> User
        Sets the owner of this User to itself. Generally used on creation
        of a new User in Mongo.
        '''

        self.set('createdBy', self.getId())
        return self

    def getAddresses(self, temporary=False):
        ''' (User) -> list of models.addresses.addresses
        Obtains a listing of Addresses owned by this User.
        '''

        return [Address(db, **address) for address in 
            self.db[Address.collection].find(
                {
                    'createdBy': self.getId(),
                    'temporary': temporary
                }
            )
        ]