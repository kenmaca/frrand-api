from flask import current_app as app

schema = {
    'banner': {
        'type': 'string',
        'required': True
    },
    'pinned': {
        'type': 'boolean',
        'default': False
    },
    'starts': {
        'type': 'datetime',
        'required': True
    },
    'ends': {
        'type': 'datetime'
    }
}

config = {
    'item_title': 'banner',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'allowed_filters': [],
    'item_methods': ['GET'],
    'resource_methods': ['GET'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    pass
