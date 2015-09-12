from flask import current_app as app

# accuracy to allow range of addresses for given coordinates
EPSILON = 0.001
DECIMAL_PLACES = 3

schema = {
    'name': {
        'type': 'string',
        'minlength': 4
    },
    'address': {
        'type': 'string',
        'regex': (
            '^[0-9]+\s[a-zA-Z0-9\s]+,'
            + '\s[a-zA-Z\s]+,'
            + '\s[A-Z]{2}\s[a-zA-Z0-9\s]+,'
            + '\s[a-zA-Z\s]+$'
        )
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
    'mongo_indexes': {
        '_id_': [('_id', 1)],
        'location_2dsphere': [('location', '2dsphere')]
    },
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_addresses += onInsert
    app.on_inserted_addresses += onInserted
    app.on_update_addresses += onUpdate

# hooks

# on_update_addresses
def onUpdate(updates, originalAddress):
    ''' (list of dict) -> NoneType
    An Eve hook used prior to update.
    '''

    # prevent changing of coordinates
    if 'location' in updates:
        abort(422, 'Coordinates are read-only')

    # prevent address changes outside boundaries
    elif 'address' in updates:
        try:
            import models.addresses as addresses
            (addresses.Address.fromObjectId(
                    app.data.driver.db,
                    originalAddress['_id']
                ).changeAddress(updates['address'], EPSILON)
            )
        except AttributeError:
            abort(
                422,
                'Address does not match coordinates within '
                + str(111 * EPSILON * 1000)
                + ' metres'
            )

# on_insert_addresses
def onInsert(insertAddresses):
    ''' (list of dict) -> NoneType
    An Eve hook used to prior to insertion.
    '''

    for address in insertAddresses:
        _approximate(address)
        _uniquePermanent(address)

# on_inserted_addresses
def onInserted(insertedAddresses):
    ''' (list of dict) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.addresses as addresses
    for address in insertedAddresses:
        (addresses.Address(
                app.data.driver.db,
                addresses.Address.collection,
                **address
            ).geocodeAddress()
            .commit()
        )

# helpers

def _approximate(address):
    ''' (dict) -> NoneType
    Approximates the address coordinates within DECIMAL_PLACES accuracy.
    '''

    address['location']['coordinates'] = [
        round(address['location']['coordinates'][0], DECIMAL_PLACES),
        round(address['location']['coordinates'][1], DECIMAL_PLACES)
    ]

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
        abort(422, 'Address already exists')
