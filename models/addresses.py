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

        # replace with more accurate name and coordinates
        if not fromCoordinates:
            geocoded = GoogleV3(api_key=PLACES_API_KEY).geocode(
                self.get('address')
            )

            if not geocoded:
                raise AttributeError('Invalid address or geocoding failure')

            self.set('address', geocoded[0]);
            point = self.get('location')
            point['coordinates'] = [geocoded[1][1], geocoded[1][0]]
            self.set('location', point)

        # get other details from coordinates
        geocoded = GoogleV3(api_key=PLACES_API_KEY).reverse(
            self.get('location')['coordinates'][::-1]
        )

        if not geocoded:
            raise AttributeError('Invalid coordinates or geocoding failure')

        # legacy one lined address
        if not self.exists('address'):
            self.set('address', geocoded[0].address)

        # components, find the first geocoded address with a route starting from most specific
        self.set('components', _splitInComponents(geocoded))

        # fail if street is not in components
        if not self.get('components').get('route'):
            raise AttributeError('Address is too vague and a street name could not be resolved')

        # approximated coordinates
        self.set(
            'approximatedCoordinates',
            [
                geocoded[1].longitude,
                geocoded[1].latitude
            ]
        )

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
            try:
                self.geocode(not self.exists('address')).commit()
            except AttributeError:
                self.set('components', {})

        # force limiting of fine detail
        if limit:
            formatted, components = self.getLimited()
            addressView['roomNumber'] = None
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

    def getOwner(self):
        ''' (Address) -> models.users.User
        Gets the owner of this Address.
        '''

        import models.users as users
        return users.User.fromObjectId(
            self.db,
            self.get('createdBy')
        )

def _splitInComponents(addresses):
    ''' (list of geopy.location.Location) -> dict
    Converts a geocoded Location into a dictionary split into components.
    '''

    for address in addresses:
        components = {}
        for component in address.raw['address_components']:
            try:
                components[component['types'][0]] = component['long_name']

                # add limited postal prefix
                if component['types'][0] == 'postal_code':
                    components['postal_code_prefix'] = component['long_name'][:3]
            except IndexError:
                pass

        # return first (most specific) address with a route present
        if 'route' in components:
            return components

    # otherwise, return the last address (likely will never reach here)
    return components
