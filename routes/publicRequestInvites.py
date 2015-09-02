from flask import current_app as app
from flask import abort

# add attribute to convert into an accepted requestInvite
schema = {
    'requestId': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        }
    },
    'from': {
        'type': 'objectid',
        'required': True,
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        }
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
    'acceptedBy': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        },
        'default': None
    }
}

config = {
    'item_title': 'publicRequestInvite',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],
    'schema': schema,
    'auth_field': None
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    pass

# on_pre_GET_publicRequestInvites
def onPreGet(request, lookup):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to a GET request.
    '''

    pass

# on_updated_publicRequestInvites
def onUpdated(changes, publicRequestInvite):
    ''' (dict, dict) -> NoneType
    An Eve hook used after a publicRequestInvite is updated.
    '''

    pass

# helpers

def _convertToAcceptedInvite(changes, publicRequestInvite):
    ''' (dict, dict) -> NoneType
    Converts an unclaimed publicRequestInvite to an accepted requestInvite.
    '''

    # ensure that parent request is really attached to this public
    # request before doing anything
    request = app.data.driver.db['requests'].find_one({
        '_id': publicRequestInvite['requestId'],
        'publicRequestInviteId': publicRequestInvite['_id']
    })

    if request:
        pass
    else:
        abort(422)
