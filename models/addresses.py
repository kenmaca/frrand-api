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
                geocoded = GoogleV3().reverse(
                    self.get('location')['coordinates'][::-1]
                )

                # legacy one lined address
                self.set('address', geocoded[0].address)

                # approximated coordinates
                self.set(
                    'approximatedCoordinates',
                    [
                        geocoded[1].latitude,
                        geocoded[1].longitude
                    ]
                )

            except Exception:

                # TODO: try another geocoding service
                self.set('address', 'Unknown')

        return self

    def view(self, limit=False):
        ''' (Address) -> dict
        Builds a view of this Address, and hides fine detail of this
        Address if limit is True.
        '''

        addressView = super().view()

        # build if it didn't exist before
        addressView['components'] = self.getComponents()

        # force limiting of fine detail
        if limit:
            formatted, components = self.getLimited()
            addressView['address'] = formatted
            addressView['components'] = components
            addressView['location']['coordinates'] = addressView.get(
                'approximatedCoordinates',
                addressView.get('location')['coordinates']
            )

        return addressView

    def getComponents(self):
        ''' (Address) -> dict
        Gets the components of this Address, or build it if it didn't
        exist before.
        '''

        if not self.exists('components'):
            try:
                self.set(
                    'components',
                    _splitInComponents(
                        GoogleV3().geocode(
                            self.get('address')
                        )
                    )
                ).commit()
            except Exception:
                self.set('components', {})

        return self.get('components')

    def getLimited(self):
        ''' (Address) -> str, dict
        Builds a limited string and component dict representing this
        Address.
        '''

        limited = {
            component: self.getComponents()[component]
            for component in self.getComponents()
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

    def changeAddress(self, address, eps):
        ''' (Address, str, float) -> Address
        Changes the address for this Address.
        '''

        try:
            geo = GoogleV3().geocode(address)
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
        except Exception:
            pass

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
