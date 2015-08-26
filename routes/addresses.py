from geopy.geocoders import GoogleV3

schema = {
    'name': {
        'type': 'string',
        'minlength': 4
    },
    'address': {
        'type': 'string',
        'regex': '^[0-9]+\s[a-zA-Z0-9\s]+,\s[a-zA-Z\s]+,\s[A-Z]{2}\s[a-zA-Z0-9\s]+,\s[a-zA-Z\s]+$'
    },
    'phone': {
        'type': 'string',
        'regex': '\D*(\d*)\D*(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$'
    },
    'location': {
        'type': 'point',
        'unique': True,
        'required': True
    },
    'placeId': {
        'type': 'string'
    }
}

config = {
    'item_title': 'address',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_addresses += fillInGeocodedAddress

# hooks

# on_insert_addresses
def fillInGeocodedAddress(addresses):
    ''' (list of dict) -> NoneType
    An Eve hook used to fill in the address if missing from a geocoding
    service.
    '''

    for address in addresses:
        if 'address' not in address:
            try:
                address['address'] = GoogleV3().reverse(
                    address['location']['coordinates'][::-1]
                )[0].address
            except Exception:

                # TODO: try another geocoding service
                address['address'] = 'Unknown'
