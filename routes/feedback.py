from flask import current_app as app

schema = {
    'requestId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        },
        'required': True,
        'readonly': True
    },
    'requestInviteId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requestInvites',
            'field': '_id'
        },
        'required': True,
        'readonly': True
    },
    'rating': {
        'type': 'integer',
        'min': 1,
        'max': 5,
        'required': True,
        'readonly': True
    },
    'comment': {
        'type': 'string',
        'maxlength': 240,
        'readonly': True,
        'default': ''
    },
    'for': {
        'type': 'objectid',
        'required': True,
        'readonly': True,
        'data_relation': {
            'resource': ''
        }
    }
}

config = {
    'item_title': 'feedback',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': ['for', 'requestId', 'requestInviteId'],
    'item_methods': ['GET'],
    'resource_methods': ['GET'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    pass