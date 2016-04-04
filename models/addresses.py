import models.orm as orm
from config import PLACES_API_KEY
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

    def geocode(self, fromCoordinates=True):
        ''' (Address) -> Address
        Fills in the address if missing from a geocoding service.
        '''

        try:
            if fromCoordinates:
                geocoded = GoogleV3(api_key=PLACES_API_KEY).reverse(
                    self.get('location')['coordinates'][::-1]
                )
            else:
                geocoded = GoogleV3(api_key=PLACES_API_KEY).geocode(
                    self.get('address')
                )

                # set coordinates for address entry method
                self.set(
                    'location',
                    [
                        geocoded[0].longitude,
                        geocoded[0].latitude,
                    ]
                )

            # legacy one lined address
            self.set('address', geocoded[0].address)

            # components
            self.set('components', _splitIntoComponents(geocoded))

            # approximated coordinates
            self.set(
                'approximatedCoordinates',
                [
                    geocoded[1].longitude,
                    geocoded[1].latitude
                ]
            )

        except Exception:
            raise AttributeError('Invalid address or geocoding failure')

        return self

    def view(self, limit=False):
        ''' (Address) -> dict
        Builds a view of this Address, and hides fine detail of this
        Address if limit is True.

        Warning: calling view may alter the Address from geocoding.
        '''

        addressView = super().view()

        # build if it didn't exist before
        if not self.exists('components'):
            self.geocode(not self.exists('address')).commit()

        # force limiting of fine detail
        if limit:
            formatted, components = self.getLimited()
            addressView['roomNumber'] = None
            addressView['buildingName'] = None
            addressView['address'] = formatted
            addressView['components'] = components
            addressView['location']['coordinates'] = addressView.get(
                'approximatedCoordinates',
                addressView.get('location')['coordinates']
            )

        return addressView

    def getLimited(self):
        ''' (Address) -> str, dict
        Builds a limited string and component dict representing this
        Address.
        '''

        limited = {
            component: self.get('components').get(component)
            for component in self.get('components')
            if component not in [
                'street_number',
                'postal_code'
            ]
        }

        return (
            '%s, %s, %s, %s, %s' % (
                limited.get('neighbourhood', limited.get('route')),
                limited.get('sublocality_level_1', limited.get('locality')),
                limited.get('administrative_area_level_1'),
                limited.get('postal_code', limited.get('postal_code_prefix')),
                limited.get('country')
            ),
            limited
        )

    def getGeo(self):
        ''' (Address) -> dict
        Gets a GeoJson representation of this Address.
        '''

        return self.get('location')

    def changeAddress(self, address):
        ''' (Address, str, float) -> Address
        Changes the address for this Address.
        '''

        self.geocode(False)
        return self

def _splitInComponents(address):
    ''' (geopy.location.Location) -> dict
    Converts a geocoded Location into a dictionary split into components.
    '''

    components = {}
    for component in address.raw['address_components']:
        try:
            components[component['types'][0]] = component['long_name']

            # add limited postal prefix
            if component['types'][0] == 'postal_code':
                components['postal_code_prefix'] = component['long_name'][:3]
        except IndexError:
            pass

    return components
