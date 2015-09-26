from flask import current_app as app

config = {
    'item_title': 'profile',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'datasource': {
        'source': 'users',
        'projection': {
            'active': 1,
            'requestsReceived': 1,
            'phone': 1,
            'phoneVerified': 1,
            'lastName': 1,
            'username': 1,
            'numberOfRatings': 1,
            'requestsDelivered': 1,
            'firstName': 1,
            'rating': 1,
            'points': 1,
            'phoneMethods': 1,
            'picture': 1,
            'isMale': 1
        }
    },
    'allowed_filters': [],
    'item_methods': ['GET'],
    'resource_methods': ['GET']
}

def init(app):
    pass
