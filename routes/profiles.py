from flask import current_app as app

config = {
    'item_title': 'profile',
    'public_methods': ['GET'],
    'public_item_methods': ['GET'],
    'datasource': {
        'source': 'users',
        'projection': {
            'password': 0,
            'salt': 0,
            'deviceId': 0,
            'phone': 0,
            'phoneMethods': 0,
            'phoneVerified': 0,
            'pendingPoints': 0,
            'createdBy': 0,
            '_verificationCode': 0
        }
    },
    'allowed_filters': [],
    'item_methods': ['GET'],
    'resource_methods': ['GET']
}

def init(app):
    pass
