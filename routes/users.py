from flask import current_app as app
from facebook import GraphAPI, GraphAPIError
import errors.users

RESERVED_USERNAMES = ['_facebook', '_google']

schema = {
    'username': {
        'type': 'string',
        'minlength': 4,
        'maxlength': 32,
        'unique': True,
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
    'firstName': {
        'type': 'string'
    },
    'lastName': {
        'type': 'string'
    },
    'isMale': {
        'type': 'boolean'
    },
    'picture': {
        'type': 'media'
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
        'default': 1000
    },
    'pendingPoints': {
        'type': 'integer',
        'readonly': True,
        'default': 0
    },
    'activated': {
        'type': 'boolean',
        'readonly': True,
        'default': False
    },
    'phone': {
        'type': 'string',
        'unique': True,
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
    },
    'deviceType': {
        'type': 'string',
        'default': 'android',
        'allowed': [
            'android',
            'ios'
        ]
    },
    'facebookAccessToken': {
        'type': 'string'
    },
    'facebookId': {
        'type': 'string',
        'unique': True,
        'readonly': True
    },
    'googleAccessToken': {
        'type': 'string'
    },
    'googleId': {
        'type': 'string',
        'unique': True,
        'readonly': True
    }
}

config = {
    'item_title': 'user',
    'public_methods': ['POST'],
    'public_item_methods': [],
    'datasource': {
        'projection': {
            'deviceId': 0,
            'password': 0,
            'salt': 0,
            '_verificationCode': 0,
            'facebookAccessToken': 0,
            'googleAccessToken': 0,
            'verifcationCode': 0
        }
    },
    'allowed_filters': [],
    'extra_response_fields': ['username'],
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    'resource_methods': ['POST'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_users += onInsert
    app.on_inserted_users += onInserted
    app.on_updated_users += onUpdated
    app.on_update_users += onUpdate

# hooks

# on_insert_users
def onInsert(insertUsers):
    ''' (list of dict) -> NoneType
    An Eve hook used prior to insertion.
    '''

    import models.users as users
    for user in insertUsers:

        # prevent reserved usernames
        if 'username' in user and user['username'] in RESERVED_USERNAMES:
            errors.users.abortUsernameReserved()

        # generate username if it wasn't specified
        else:
            user['username'] = users.User.generateUsername(
                app.data.driver.db
            )

        # validate facebook access token
        if 'facebookAccessToken' in user:
            _getFacebook(user['facebookAccessToken'], user)

# on_inserted_users
def onInserted(insertedUsers):
    ''' (list of dict) -> NoneType
    An Eve hook used to set the createdBy field for an newly
    inserted user document to itself (since Eve handles
    auth_field only when inserting via Authenticated routes).
    '''

    import models.users as users
    for userDict in insertedUsers:

        # set newly created user as self-owning
        user = users.User(
            app.data.driver.db,
            users.User.collection,
            **userDict
        ).selfOwn()

        # encrypt password
        user.setPassword(user.get('password'))

        # send verification message if phone included
        if user.exists('phone'):
            user.changePhoneNumber(user.get('phone'))

        user.commit()

# on_update_users
def onUpdate(changes, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used before update.
    '''

    # prevent usage of reserved names
    if 'username' in changes and changes['username'] in RESERVED_USERNAMES:
        errors.users.abortUsernameReserved()

    # validate facebook access token
    if 'facebookAccessToken' in changes:
        _getFacebook(changes['facebookAccessToken'], changes)

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

# helpers
def _getFacebook(accessToken, userDict):
    ''' (str, dict) -> (str, str, str, str)
    Gets the id, first_name, last_name, and gender for the Facebook user
    associated with accessToken, respectively. Also mutates the provided user
    dict with these values obtained.
    '''

    try:
        fb = GraphAPI(accessToken, version='2.2')
        user = fb.get_object(
            'me?fields=first_name,last_name,gender'
        )

        # mutate the dict for insertion/update
        userDict['facebookId'] = user['id']
        userDict['firstName'] = user['first_name']
        userDict['lastName'] = user['last_name']
        userDict['isMale'] = user['gender'] == 'male'

        # prevent duplicate association
        try:
            import models.users as users
            users.User.findOne(
                app.data.driver.db,
                facebookId=userDict['facebookId']
            )

            # exit since we found something
            errors.users.abortFacebookDuplicateAccount()
        except KeyError: pass

        # store photo locally (allow failure if image doesn't exist)
        try:
            picture = fb.get_object(
                'me/picture?type=large'
            )

            # now store it
            userDict['picture'] = app.media.put(
                picture['data'],
                content_type=picture['mime-type']
            )

        except GraphAPIError:
            pass

        return (
            user['id'],
            user['first_name'],
            user['last_name'],
            user['gender']
        )

    except GraphAPIError:
        errors.users.abortFacebookInvalidToken()
