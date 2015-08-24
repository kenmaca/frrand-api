from flask import current_app as app
from flask import abort
from eve.methods.post import post_internal
from datetime import datetime
from pytz import UTC
from bson import ObjectId
from lib.gcm import gcmSend
from . requestInvites import embedRequestInviteDisplay

schema = {
    'items': {
        'type': 'list',
        'minlength': 1,
        'required': True,
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string',
                    'required': True
                },
                'description': {
                    'type': 'string'
                },
                'quantity': {
                    'type': 'integer',
                    'default': 1
                },
                'price': {
                    'type': 'number',
                    'default': 0
                }
            }
        }
    },
    'places': {
        'type': 'list',
        'minlength': 1,
        'required': True,
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string',
                    'required': True
                },
                'address': {
                    'type': 'string',
                    'required': True
                },
                'location': {
                    'type': 'point',
                    'required': True
                },
                'phone': {
                    'type': 'string'
                },
                'placeId': {
                    'type': 'string'
                }
            }
        }
    },
    'requestedTime': {
        'type': 'datetime',
        'required': True
    },
    'inviteIds': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'requestInvites',
                'field': '_id'
            }
        },
        'default': []
    },
    'attachedInviteId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requestInvites',
            'field': '_id'
        },
        'default': None
    },
    'destination': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'addresses',
            'field': '_id'
        },

        # TODO: remove this and make mandatory when implemented on client side
        'default': None
    }
}

config = {
    'item_title': 'request',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': [],
    'resource_methods': ['GET', 'POST'],
    'item_methods': ['GET', 'PATCH'],
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_requests += generateRequestInvites
    app.on_pre_GET_requests += forceFetchNewRequests
    app.on_fetched_item_requests += embedRequestDisplay

# hooks

# on_pre_GET_requests
def forceFetchNewRequests(request, lookup):
    ''' (Request, dict) -> NoneType
    An Eve hook used to force a fresh fetch when requesting a
    request document.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        res = app.data.driver.db['requests'].update(
            {'_id': ObjectId(lookup['_id'])},
            {'$set': {'_updated': datetime.utcnow()}},
            upsert=False, multi=False
        )

# on_fetched_item_requests
def embedRequestDisplay(request):
    ''' (dict) -> NoneType
    An Eve hook used to embed requestInvites to its parent request
    as well as prune the expired and unaccepted invites.
    '''

    pendingInvites = []
    if 'inviteIds' in request:
        for inviteId in request['inviteIds']:
            requestInvite = app.data.driver.db['requestInvites'].find_one({
                '_id': inviteId
            })

            # not accepted and expired, so remove the requestInvite
            if ((requestInvite['requestExpiry']
                < datetime.utcnow().replace(tzinfo=UTC))
                and (not requestInvite['accepted'])
            ):

                # remove actual requestInvite
                app.data.driver.db['requestInvites'].remove({
                    '_id': inviteId
                })
            else:
                pendingInvites.append(requestInvite)

        # update list of tracked requestInvites in parent request
        app.data.driver.db['requests'].update(
            {'_id': request['_id']},
            {'$set': {'inviteIds':
                [invite['_id'] for invite in pendingInvites]
            }},
            upsert=False, multi=False
        )

        # finally, replace output list of invites with embedded ones
        request['inviteIds'] = pendingInvites

# on_inserted_requests
def generateRequestInvites(requests):
    ''' (dict) -> NoneType
    An Eve hook used to automatically generate RequestInvites for
    the given Requests and sends out the RequestInvite via GCM.
    '''

    invitesGenerated = []

    # currently just sends out to ALL users (for dev use only)
    # TODO: perform candidate matching here
    users = app.data.driver.db['users'].find({})
    for request in requests:
        for user in users:
            with app.test_request_context():

                # adding to list of inviteIds is dependant on
                # on_inserted_requestInvites to get _id
                resp = post_internal('requestInvites', {
                    'requestId': request['_id'],
                    'location': {
                        'type': 'Point',
                        'coordinates': [0.0, 0.0]
                    },
                    'from': request['createdBy']
                })

                # set ownership of invite to invitee
                app.data.driver.db['requestInvites'].update(
                    {'_id': resp[0]['_id']},
                    {'$set': {'createdBy': user['_id']}},
                    upsert=False, multi=False
                )

                # get updated requestInvite
                requestInvite = app.data.driver.db['requestInvites'].find_one(
                    {'_id': resp[0]['_id']}
                )

                # add this invite to the parent request list
                invitesGenerated.append(requestInvite['_id'])

                # embed parent request to the newly created requestInvite
                embedRequestInviteDisplay(requestInvite)

                # and finally, send gcm out
                gcmSend(user['deviceId'], {
                    'type': 'requestInvite',
                    'requestInvite': requestInvite['_id']
                })

        # update list of inviteIds in Mongo
        app.data.driver.db['requests'].update(
            {'_id': request['_id']},
            {'$set': {'inviteIds': invitesGenerated}},
            upsert=False, multi=False
        )
