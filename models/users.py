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

        return gcm.gcmSend(
            deviceId if deviceId else self.get('deviceId'),
            {
                'type': messageType,
                messageType: message
            }
        )

    def useAPIKey(self, apiKey):
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
            import models.locations as location
            return locations.Location.findOne(
                self.db,
                createdBy=self.getId()
            )
        except ValueError:
            return
