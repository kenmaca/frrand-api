from routes.requestInvites import (schema, forceFetchNewRequestInvites,
    embedRequestInviteDisplay)
from flask import current_app as app
from flask import abort
from utils.auth import NoAuth

# remove irrelevant schema
del schema['requestExpiry']
del schema['accepted']
del schema['attached']

# add attribute to convert into an accepted requestInvite
schema['acceptedBy'] = {
    'type': 'objectid',
    'data_relation': {
        'resource': 'users',
        'field': '_id'
    },
    'default': None
}

config = {
    'item_title': 'publicRequestInvite',
    'public_methods': ['GET'],
    'public_item_methods': ['GET', 'PATCH'],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],
    'schema': schema,
    'authentication': NoAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_pre_GET_publicRequestInvites += onPreGet
    app.on_fetched_item_publicRequestInvites += embedRequestInviteDisplay
    app.on_updated_publicRequestInvites += onUpdated

# on_pre_GET_publicRequestInvites
def onPreGet(request, lookup):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to a GET request.
    '''

    forceFetchNewRequestInvites(request, lookup, 'publicRequestInvites')

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
