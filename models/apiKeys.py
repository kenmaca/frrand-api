import models.orm as orm

class APIKey(orm.MongoORM):
    ''' A representation of an APIKey in Frrand.
    '''

    collection = 'apiKeys'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> APIKey
        Creates a APIKey directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, APIKey)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> APIKey
        Finds a single APIKey given query.
        '''

        return orm.MongoORM.findOne(db, APIKey, **query)

    def prune(self):
        ''' (APIKey) -> APIKey
        Removes any other APIKeys with the same deviceId to maintain a 1-to-1
        pairing of deviceIds to apiKeys.
        '''

        [APIKey(self.db, APIKey.collection, **apiKey).remove() for apiKey
            in self.source.find({
                'deviceId': self.get('deviceId'),
                '_id': {
                    '$ne': self.getId()
                }
            })
        ]

        return self
