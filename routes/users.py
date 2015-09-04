from flask import current_app as app
from models.users import User

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
    'phone': {
        'type': 'string'
    },
    'phoneMethods': {
        'type': 'list',
        'allowed': [
            'sms',
            'phone'
        ],
        'dependencies': [
            'phone'
        ]
    },
    'phoneVerified': {
        'type': 'boolean',
        'readonly': True
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
            'username': 1,
            'active': 1
        }
    },
    'allowed_filters': [],
    'item_methods': ['GET', 'PATCH'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_users += onInserted

# hooks

# on_inserted_users
def onInserted(users):
    ''' (list of dict) -> NoneType
    An Eve hook used to set the createdBy field for an newly
    inserted user document to itself (since Eve handles
    auth_field only when inserting via Authenticated routes).
    '''

    for user in users:

        # set newly created user as self-owning
        User(app.driver.db['users'], **user).selfOwn().commit()
