from flask import current_app as app

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
    'requestsRecieved': {
        'type': 'integer',
        'readonly': True,
        'default': 0
    },
    'requestsDelivered': {
        'type': 'integer',
        'readonly': True,
        'default': 0
    },
    'rating': {
        'type': 'float',
        'readonly': True,
        'default': 0
    },
    'numberOfRatings': {
        'type': 'integer',
        'readonly': True,
        'default': 0
    },
    'points': {
        'type': 'integer',
        'readonly': True,
        'default': 1
    },
    'pendingPoints': {
        'type': 'integer',
        'readonly': True,
        'default': 0
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
def onInserted(insertedUsers):
    ''' (list of dict) -> NoneType
    An Eve hook used to set the createdBy field for an newly
    inserted user document to itself (since Eve handles
    auth_field only when inserting via Authenticated routes).
    '''

    import models.users as users
    for user in insertedUsers:

        # set newly created user as self-owning
        users.User(
            app.data.driver.db,
            users.User.collection,
            **user
        ).selfOwn().commit()
