from flask import current_app as app

schema = {
    'requestId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        },
        'required': True
    },
    'requestInviteId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requestInvites',
            'field': '_id'
        },
        'required': True
    },
    'rating': {
        'type': 'integer',
        'min': 1,
        'max': 5,
        'required': True
    }
    'comment': {
        'type': 'string',
        'maxlength': 240
    },
    'for': {
        'type': 'objectid',
        'data_relation': {
            'resource': ''
        }
    }
}

config = {
    'item_title': 'feedback',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': ['for'],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}