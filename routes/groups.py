from flask import current_app as app

schema = {
    'name': {
        'type': 'string',
        'unique': True,
        'required': True
    },
    'admins': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'users',
                'field': '_id'
            }
        },
        'default': []
    },
    'logo': {
        'type': 'media'
    },
    'cover': {
        'type': 'media'
    },
    'deliveries': {
        'type': 'integer',
        'default': 0,
        'readonly': True
    }
}

config = {
    'item_title': 'group',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'auth_field': None,
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    pass
