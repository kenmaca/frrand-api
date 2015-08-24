schema = {
    'name': {
        'type': 'string',
        'minlength': 4
    },
    'address': {
        'type': 'string',
        'regex': '^[0-9]+\s[a-zA-Z0-9\s]+,\s[a-zA-Z\s]+,\s[A-Z]{2}\s[a-zA-Z0-9\s]+,\s[a-zA-Z\s]+$',
        'required': True
    },
    'phone': {
        'type': 'string',
        'regex': '\D*(\d*)\D*(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$'
    },
    'location': {
        'type': 'point',
        'required': True
    },
    'placeId': {
        'type': 'string'
    }
}

config = {
    'item_title': 'address',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    pass
