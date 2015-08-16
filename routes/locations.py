schema = {
    'lngLat': {
        'type': 'point',
        'required': True
    }
}

config = {
    'item_title': 'location',
    'public_methods': ['GET'],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}
