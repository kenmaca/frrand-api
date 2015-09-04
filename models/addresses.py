from models.orm import MongoORM

class Address(MongoORM):
    ''' A representation of an Address in Frrand.
    '''

    collection = 'addresses'

    def __init__(self, db, **fields):
        ''' (Address, pymongo.database.Database) -> Address
        Instantiates a new Address.
        '''

        MongoORM.__init__(self, db, Address.collection, **fields)

    @staticmethod
    def fromObjectId(source, objectId):
        ''' (bson.ObjectId) -> Address
        Creates an Address directly from database with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(source, objectId, Address)