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

    app.on_insert_apiKeys += provisionApiKey
    app.on_insert_apiKeys += pruneStaleApiKeys

# hooks

# on_insert_apiKeys
def provisionApiKey(apiKeys):
    ''' (dict) -> NoneType
    An Eve hook used to generate an apiKey from a document that is about
    to be inserted containing a deviceId.

    REQ: documents was inserted via an Authenticated route,
    dependant on the createdBy auth_field
    '''

    for key in apiKeys:
        apiKey = (''.join(random.choice(string.ascii_uppercase)
            for x in range(32)))

        # only insert into MongoDB if GCM went through
        if (gcmSend(key['deviceId'], {
            'type': 'apiKey',
            'apiKey': {
                'apiKey': apiKey,
                'userId': key['createdBy']
            }
        })):

            # inject generated apiKey to doc
            key['apiKey'] = apiKey
        else:
            abort(422)

# on_insert_apiKeys
def pruneStaleApiKeys(apiKeys):
    ''' (dict) -> NoneType
    An Eve hook used to remove any other apiKeys with the same
    deviceId as newly inserted ones to maintain a 1-to-1 pairing
    of deviceIds to apiKeys.
    '''

    for apiKey in apiKeys:
        app.data.driver.db['apiKeys'].remove({
            'deviceId': apiKey['deviceId']
        })
