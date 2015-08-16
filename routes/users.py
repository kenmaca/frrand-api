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
    'deviceId': {
        'type': 'string',
        'required': True
    }
}

config = {
    'item_title': 'user',
    'auth_field': 'createdBy',
    'public_methods': ['GET', 'POST'],
    'public_item_methods': [],
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'username'
    },
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}
