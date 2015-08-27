from pymongo import MongoClient
from .. config import *

class Database(MongoClient):
    ''' A connection to the MongoDB database.
    '''

    def __init__(self):
        ''' (Database) -> NoneType
        Creates a connection to this Database.
        '''

        super(Database, self).__init__(
            'mongodb://%s:%s@%s:%d/%s' % (
                MONGO_USERNAME,
                MONGO_PASSWORD,
                MONGO_HOST,
                MONGO_PORT,
                MONGO_DBNAME
            )
        )

    def __getattr__(self, attr):
        ''' (Database, str) -> pymongo.database.Database
        Gets a Database from Mongo.
        '''
        
        return super(Database, self).__getattr__(
            MONGO_DBNAME if attr == 'db' else attr
        )

# import this instance
db = Database()
