from flask import current_app as app
from flask import abort
from datetime import datetime, timedelta
from pytz import UTC
from bson import ObjectId
from lib.gcm import gcmSend
from eve.methods.patch import patch_internal

# default expiry time of each requestInvite until deletion in minutes
DEFAULT_EXPIRY = 15

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
    'requestExpiry': {
        'type': 'datetime',
        'readonly': True
    },
    'createdBy': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        }
    },
    'accepted': {
        'type': 'boolean',
        'default': False
    },
    'attached': {
        'type': 'boolean',
        'default': False,
        'readonly': True
    }
}

config = {
    'item_title': 'requestInvite',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH', 'DELETE'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_pre_GET_requestInvites += forceFetchNewRequestInvites
    app.on_fetched_item_requestInvites += embedRequestInviteDisplay
    app.on_insert_requestInvites += requestInviteExpiry
    app.on_update_requestInvites += allowAcceptanceOfRequestInvite
    app.on_updated_requestInvites += alertOwnerOfAcceptedRequestInvite
    app.on_deleted_item_requestInvites += removeFromParentRequest

# hooks

# on_pre_GET_requestInvites
def forceFetchNewRequestInvites(request, lookup):
    ''' (Request, dict) -> NoneType
    An Eve hook used to force a fresh fetch when requesting a
    requestInvite document.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        res = app.data.driver.db['requestInvites'].update(
            {'_id': ObjectId(lookup['_id'])},
            {'$set': {'_updated': datetime.utcnow()}},
            upsert=False, multi=False
        )

# on_fetched_item_requestInvites
def embedRequestInviteDisplay(request):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    request is mutated with new values.
    '''

    # embed parent request
    request['requestId'] = app.data.driver.db['requests'].find_one(
        {'_id': request['requestId']}
    )

    # embed destination in parent request
    if 'destination' in request['requestId']:
        address = app.data.driver.db['addresses'].find_one({
            '_id': request['requestId']['destination']
        })

        request['requestId']['destination'] = address

    # embed from (only username here, do not provide entire document)
    request['from'] = app.data.driver.db['users'].find_one(
        {'_id': request['from']}
    )['username']    

# on_insert_requestInvites
def requestInviteExpiry(requestInvites):
    ''' (dict) -> NoneType
    An Eve hook used to add an expiry time of 15 minutes to each
    requestInvite.
    '''

    for requestInvite in requestInvites:
        requestInvite['requestExpiry'] = datetime.utcnow() + timedelta(
            minutes=DEFAULT_EXPIRY
        )

# on_update_requestInvites
def allowAcceptanceOfRequestInvite(changes, requestInvite):
    ''' (dict) -> NoneType
    An Eve hook used to determine if a requestInvite can be accepted or not
    by its requestExpiry < currentTime.
    '''

    if (('accepted' in changes)
        and (changes['accepted'] and not requestInvite['accepted'])
    ):
        if (requestInvite['requestExpiry']
            < datetime.utcnow().replace(tzinfo=UTC)
        ):

            # invite has expired, force unacceptable
            abort(422)

    # once accepted, disallow any changes
    elif (('accepted' in changes)
        and (requestInvite['accepted'])
    ):
        abort(422)

# on_updated_requestInvites
def alertOwnerOfAcceptedRequestInvite(changes, requestInvite):
    ''' (dict) -> NoneType
    An Eve hook used to alert the request owner of a requestInvite that was
    successfully accepted by the invitee.
    '''

    if (('accepted' in changes)
        and (changes['accepted'] and not requestInvite['accepted'])
    ):
        requestOwner = app.data.driver.db['users'].find_one({
            '_id': requestInvite['from']
        })

        # alert request owner of the acceptance
        gcmSend(requestOwner['deviceId'], {
            'type': 'requestInviteAccepted',
            'requestInviteAccepted': requestInvite['_id']
        })

# on_deleted_item_requestInvites
def removeFromParentRequest(requestInvite):
    ''' (dict) -> NoneType
    An Eve hook used to remove the requestInvite from the parent request.
    '''

    request = app.data.driver.db['requests'].find_one(
        {'_id': requestInvite['requestId']}
    )

    # remove from parent request if it exists in its list
    if (request) and (requestInvite['_id'] in request['inviteIds']):
        request['inviteIds'].remove(requestInvite['_id'])

        # now, update the parent request in Mongo
        patch_internal(
            'requests',
            {'inviteIds': request['inviteIds']},
            _id=requestInvite['requestId']
        )
