schema = {
    'username': {
        'type': 'string',
        'minlength': 4,
        'maxlength': 18,
        'required': True,
        'unique': True
    },
    'password': {
        'type': 'string',
        'minlength': 6,
        'maxlength': 100,
        'required': True
    },
    'active': {
        'type': 'boolean',
        'default': True
    },

    # will be updated on auth success, but does not
    # guarantee that the deviceId is valid and contactable
    'deviceId': {
        'type': 'string',
        'required': True
    }
}

config = {
    'item_title': 'user',
    'public_methods': ['GET', 'POST'],
    'public_item_methods': [],
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'username'
    },
    'datasource': {
        'projection': {
            'username': 1
        }
    },
    'allowed_filters': [],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}
