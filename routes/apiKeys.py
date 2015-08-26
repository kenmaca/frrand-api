from utils.auth import UserAuth
from flask import current_app as app
from flask import abort
from lib.gcm import gcmSend
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
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['POST'],
    'schema': schema,
    'authentication': UserAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_apiKeys += onInsert

# hooks

# on_insert_apiKeys
def onInsert(apiKeys):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for apiKey in apiKeys:
        _prune(apiKey)
        _provision(apiKey)

# helpers

def _provision(apiKey):
    ''' (dict) -> NoneType
    Generates an apiKey for a given deviceId and user.
    '''

    token = (''.join(random.choice(string.ascii_uppercase)
        for x in range(32)))

    # only insert into MongoDB if GCM went through
    if (gcmSend(apiKey['deviceId'], {
        'type': 'apiKey',
        'apiKey': {
            'apiKey': token,
            'userId': apiKey['createdBy']
        }
    })):

        # inject generated apiKey to doc
        apiKey['apiKey'] = token
    else:
        abort(422)

def _prune(apiKey):
    ''' (dict) -> NoneType
    Removes any other apiKeys with the same deviceId to 
    maintain a 1-to-1 pairing of deviceIds to apiKeys.
    '''

    # remove the actual key
    app.data.driver.db['apiKeys'].remove({
        'deviceId': apiKey['deviceId']
    })
