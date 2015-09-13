from flask import current_app as app

schema = {
    'username': {
        'type': 'string',
        'minlength': 4,
        'maxlength': 32,
        'unique': True
    },
    'password': {
        'type': 'string',
        'minlength': 6,
        'maxlength': 100,
        'required': True
    },
    'salt': {
        'type': 'string',
        'readonly': True
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
        'type': 'string',
        'required': True
    },
    'phoneMethods': {
        'type': 'list',
        'allowed': [
            'sms',
            'phone'
        ],
        'dependencies': [
            'phone'
        ],
        'default': [
            'sms',
            'phone'
        ]
    },
    'phoneVerified': {
        'type': 'boolean',
        'readonly': True
    },
    'verificationCode': {
        'type': 'string'
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
    'public_item_methods': ['DELETE'],
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'username'
    },
    'datasource': {
        'projection': {
            'password': 0,
            'salt': 0,
            'deviceId': 0
        }
    },
    'allowed_filters': [],
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    'resource_methods': ['GET', 'POST'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_users += onInserted
    app.on_updated_users += onUpdated

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
        user = users.User(
            app.data.driver.db,
            users.User.collection,
            **user
        ).selfOwn()

        # generate username if missing
        user.setUsername()
        
        # encrypt password
        user.setPassword(user.get('password'))

        # send verification message if phone included
        if user.exists('phone'):
            user.changePhoneNumber(user.get('phone'))

        user.commit()

# on_updated_users
def onUpdated(changes, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used after update.
    '''

    import models.users as users
    user = users.User.fromObjectId(
        app.data.driver.db,
        original['_id']
    )

    # phone has changed, so reset verify
    if 'phone' in changes:
        user.changePhoneNumber(changes['phone']).commit()

    # attempting to verify phone
    if 'verificationCode' in changes:
        user.verifyPhone().commit()

    # if username has been changed
    if 'username' in changes:
        user.setUsername(changes['username']).commit()
