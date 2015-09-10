import models.orm as orm
import lib.gcm as gcm
from pymongo import DESCENDING

class User(orm.MongoORM):
    ''' A representation of an User in Frrand.
    '''

    collection = 'users'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> User
        Creates a User directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, User)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> User
        Finds a single User given query.
        '''

        return orm.MongoORM.findOne(db, User, **query)

    def selfOwn(self):
        ''' (User) -> User
        Sets the owner of this User to itself. Generally used on creation
        of a new User in Mongo.
        '''

        self.set('createdBy', self.getId())
        return self

    def getAddresses(self, temporary=False):
        ''' (User, bool) -> list of models.addresses.Address
        Obtains a listing of Addresses owned by this User.
        '''

        import models.addresses as addresses
        return [addresses.Address(
                self.db,
                addresses.Address.collection,
                **address
            ) for address in 
            self.db[addresses.Address.collection].find(
                {
                    'createdBy': self.getId(),
                    'temporary': temporary
                }
            )
        ]

    def message(self, messageType, message, deviceId=False):
        ''' (User, str, object) -> bool
        Sends a message to the last known device via GCM, or else
        deviceId if provided.
        '''

        if deviceId:
            return gcm.gcmSend(
                deviceId if deviceId else self.get('deviceId'),
                {
                    'type': messageType,
                    messageType: message
                }
            )

        # sends to all known devices for dev use
        else:
            return [
                gcm.gcmSend(
                    apiKey.get('deviceId'),
                    {
                        'type': messageType,
                        messageType: message
                    }
                ) for apiKey in self.getApiKeys()
            ]

    def getApiKeys(self):
        ''' (User) -> list of models.apiKeys.APIKey
        Gets all APIKeys owned by this User.
        '''

        keys = []
        import models.apiKeys as apiKeys
        for apiKey in self.source.find({'createdBy': self.getId()}):
            keys.append(
                apiKeys.APIKey(
                    self.db,
                    apiKeys.APIKey.collection,
                    **apiKey
                )
            )

        return keys

    def useApiKey(self, apiKey):
        ''' (User, models.apikeys.APIKey) -> User
        Updates the last known deviceId for this User.
        '''

        self.set('deviceId', apiKey.get('deviceId'))
        return self

    def isActive(self):
        ''' (User) -> bool
        Determines whether or not this User is accepting request invites.
        '''

        return self.get('active')

    def getLastLocation(self):
        ''' (User) -> models.locations.Location
        Gets the last reported Location for this User.
        '''

        try:
            import models.locations as locations
            return locations.Location.findOne(
                self.db,
                createdBy=self.getId()
            )
        except ValueError:
            return
