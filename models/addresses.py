import models.orm as orm
from geopy.geocoders import GoogleV3

class Address(orm.MongoORM):
    ''' A representation of an Address in Frrand.
    '''

    collection = 'addresses'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Address
        Creates an Address directly from db with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Address)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Address
        Finds a single Address given query.
        '''

        return orm.MongoORM.findOne(db, Address, **query)

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
                self.set('address', 'Unknown')

        return self

    def getGeo(self):
        ''' (Address) -> dict
        Gets a GeoJson representation of this Address.
        '''

        return self.get('location')

    def changeAddress(self, address, eps):
        ''' (Address, str, float) -> Address
        Changes the address for this Address.
        '''

        geo = GoogleV3().geocode(address)
        print(geo.longitude)
        print(self.get('location')['coordinates'][0])
        print(geo.latitude)
        print(self.get('location')['coordinates'][1])

        if (
            (
                abs(geo.longitude - self.get('location')['coordinates'][0]) 
                <= eps
            ) and (
                abs(geo.latitude - self.get('location')['coordinates'][1])
                <= eps
            )
        ):
            self.set('address', address)
        else:
            raise AttributeError('Address not within the allowed boundaries')

        return self
