schema = {
    'items': {
        'type': 'list',
        'minlength': 1,
        'required': True,
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string',
                    'required': True
                },
                'description': {
                    'type': 'string'
                },
                'quantity': {
                    'type': 'integer',
                    'default': 1
                },
                'price': {
                    'type': 'number',
                    'default': 0
                }
            }
        }
    },
    'places': {
        'type': 'list',
        'minlength': 1,
        'required': True,
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string',
                    'required': True
                },
                'address': {
                    'type': 'string',
                    'required': True
                },
                'location': {
                    'type': 'point',
                    'required': True
                },
                'phone': {
                    'type': 'string'
                },
                'placeId': {
                    'type': 'string'
                }
            }
        }
    },
    'requestedTime': {
        'type': 'datetime',
        'required': True
    }
}

config = {
    'item_title': 'request',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}
