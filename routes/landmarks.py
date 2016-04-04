from flask import current_app as app

schema = {
    'names': {
        'type': 'list',
        'schema': {
            'type': 'string'
        }
    },
    'address': {
        'type': 'string'
    },
    'buildingName': {
        'type': 'string'
    },
    'roomNumber': {
        'type': 'string'
    },
    'location': {
        'type': 'point'
    }
}

config = {
    'item_title': 'landmark',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'allowed_filters': [],
    'item_methods': ['GET'],
    'resource_methods': ['GET'],
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

    pass
