from flask import current_app as app, g
import errors.addresses

# accuracy to allow range of addresses for given coordinates
EPSILON = 0.001
DECIMAL_PLACES = 3

schema = {
    'name': {
        'type': 'string',
        'minlength': 1,
        'default': 'work'
    },
    'address': {
        'type': 'string'
    },
    'components': {
        'type': 'dict',
        'valueschema': {
            'type': 'string'
        },
        'propertyschema': {
            'type': 'string'
        }
    },
    'buildingName': {
        'type': 'string'
    },
    'roomNumber': {
        'type': 'string'
    },
    'phone': {
        'type': 'string'
    },
    'location': {
        'type': 'point',
        'required': True
    },
    'approximatedCoordinates': {
        'type': 'list',
        'readonly': True,
        'schema': {
            'type': 'float'
        }
    },
    'placeId': {
        'type': 'string'
    },
    'temporary': {
        'type': 'boolean',
        'default': False
    }
}

config = {
    'item_title': 'address',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': ['temporary'],
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

    app.on_updated_addresses += onUpdated
    app.on_inserted_addresses += onInserted

# hooks

# on_updated_addresses
def onUpdated(changes, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used after update.
    '''

    import models.addresses as addresses
    try:
        address = addresses.Address(
            app.data.driver.db,
            addresses.Address.collection,
            **original
        ).update(changes).geocode(not changes.get('address'))
    except Exception:
        errors.addresses.abortUnknownAddress()

# on_inserted_addresses
def onInserted(insertedAddresses):
    ''' (list of dict) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.addresses as addresses
    for address in insertedAddresses:
        try:
            address = addresses.Address(
                app.data.driver.db,
                addresses.Address.collection,
                **address
            ).geocode(not address.get('address'))

            # set to home address if first address created
            if not address.getOwner().getAddresses():
                address.set('name', 'home')

            address.commit()
        except Exception:
            errors.addresses.abortUnknownAddress()
