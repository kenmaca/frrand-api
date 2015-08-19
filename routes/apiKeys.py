from utils.auth import UserAuth

schema = {
    'deviceId': {
        'type': 'string',
        'minlength': 10,
        'required': True
    },
    'createdBy': {
        'type': 'objectid'
    },
    'apiKey': {
        'type': 'string',
        'readonly': True
    }
}

config = {
    'item_title': 'apiKey',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['POST'],
    'schema': schema,
    'authentication': UserAuth
}
