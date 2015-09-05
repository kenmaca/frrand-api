from models.orm import MongoORM
from geopy.geocoders import GoogleV3

class Address(MongoORM):
    ''' A representation of an Address in Frrand.
    '''

    collection = 'addresses'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Address
        Creates an Address directly from db with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(db, objectId, Address)

    def geocodeAddress(self):
        ''' (Address) -> Address
        Fills in the address if missing from a geocoding service.
        '''

        if not self.exists('address'):
            try:
                self.set(
                    'address',
                    GoogleV3().reverse(
                        self.get('location')['coordinates'][::-1]
                    )[0].address
                )
            except Exception:

                # TODO: try another geocoding service
                address['address'] = 'Unknown'

        return self
