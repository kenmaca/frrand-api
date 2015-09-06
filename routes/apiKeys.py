from utils.auth import UserAuth
from flask import current_app as app
from flask import abort
from models.apikeys import APIKey
from models.users import User
import random
import string

schema = {
    'deviceId': {
        'type': 'string',
        'minlength': 10,
        'required': True
    },
    'createdBy': {
        'type': 'objectid'
    },
    'apiKey': {
        'type': 'string',
        'readonly': True
    }
}

config = {
    'item_title': 'apiKey',
    'public_methods': ['GET'],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['POST', 'GET'],
    'schema': schema,
    'authentication': UserAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_apiKeys += onInsert
    app.on_inserted_apiKeys += onInserted

# hooks

# on_insert_apiKeys
def onInsert(apiKeys):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for apiKey in apiKeys:
        _provision(apiKey)

# on_inserted_apiKeys
def onInserted(apiKeys):
    ''' (list of dicts) -> NoneType
    An Eve hook used after insertion.
    '''

    for apiKey in apiKeys:
        APIKey(app.data.driver.db, APIKey.collection, **apiKey).prune()

# helpers

def _provision(apiKey):
    ''' (dict) -> NoneType
    Generates an apiKey for a given deviceId and user.
    '''

    token = (''.join(random.choice(string.ascii_uppercase)
        for x in range(32)))
    user = User.fromObjectId(app.data.driver.db, apiKey['createdBy'])

    # only insert into MongoDB if GCM went through
    if user.message(
        'apiKey',
        {
            'apiKey': token,
            'userId': user.getId()
        },
        apiKey['deviceId']
    ):

        # inject generated apiKey to doc
        apiKey['apiKey'] = token
    else:
        abort(422)