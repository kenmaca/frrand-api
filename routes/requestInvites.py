from utils.auth import NoAuth

schema = {
    'requestId': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'requests',
            'field': '_id',
            'embeddable': True,
        }
    },
    'location': {
        'type': 'point',
        'required': True
    },
    'from': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'users',
            'field': '_id',
            'embeddable': True,
        }
    },
    'createdBy': {
        'type': 'objectid',
        'required': True
    }
}

config = {
    'item_title': 'requestInvite',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'embedded_fields': ['requestId', 'from'],
    'schema': schema,
    'authentication': NoAuth
}
