from geopy.geocoders import GoogleV3

# accuracy to allow range of addresses for given coordinates
EPSILON = 0.01

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
        'required': True
    },
    'placeId': {
        'type': 'string'
    },
    'temporary': {
        'type': 'boolean',
        'readonly': True,
        'default': False
    }
}

config = {
    'item_title': 'address',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_addresses += onInsert
    app.on_update_addresses += onUpdate

# hooks

# on_update_addresses
def onUpdate(updates, originalAddress):
    ''' (list of dict) -> NoneType
    An Eve hook used prior to update.
    '''

    _coordinatesReadOnly(updates)
    _verifyAddress((lambda a, b: a.update(b) or a)(
        originalAddress,
        updates
    ))

# on_insert_addresses
def onInsert(addresses):
    ''' (list of dict) -> NoneType
    An Eve hook used to prior to insertion.
    '''

    for address in addresses:
        _uniquePermanent(address)
        _fillInGeocodedAddress(address)

# helpers

def _uniquePermanent(address):
    ''' (dict) -> NoneType
    Prevent duplicate permanent addresses (based on coordinates).
    '''

    # this functionality can be replaced with unique_to_user from Eve
    # in v0.6
    existing = app.data.driver.db['addresses'].find_one({
        'createdBy': address['createdBy'],
        'location': address['location'],
        'temporary': False
    })

    if existing:
        abort(422)

def _fillInGeocodedAddress(address):
    ''' (dict) -> NoneType
    Fills in the address if missing from a geocoding service.
    '''

    if 'address' not in address:
        try:
            address['address'] = GoogleV3().reverse(
                address['location']['coordinates'][::-1]
            )[0].address
        except Exception:

            # TODO: try another geocoding service
            address['address'] = 'Unknown'
    else:
        _verifyAddress(address)

def _verifyAddress(address):
    ''' (dict) -> NoneType
    Verifies if the address on insert/update matches the address's
    coordinates.
    '''

    geocoded = GoogleV3().geocode(address['address'])
    if not ((abs(geocoded.longitude - address['location']['coordinates'][0])
            < EPSILON)
        and (abs(geocoded.latitude - address['location']['coordinates'][1])
            < EPSILON)
    ):

        # do not allow totally off addresses to coordinates (within 1.1km)
        abort(422)

def _coordinatesReadOnly(addressChanges):
    ''' (dict) -> NoneType
    Prevents any changes to an address's coordinates.
    '''

    if 'location' in addressChanges:
        abort(422)
