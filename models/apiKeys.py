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
