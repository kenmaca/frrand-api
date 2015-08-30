from flask import current_app as app
from flask import abort
from eve.methods.post import post_internal
from datetime import datetime
from pytz import UTC
from bson import ObjectId
from lib.gcm import gcmSend
from pymongo import DESCENDING

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
    'candidates': {
        'type': 'list',
        'schema': {
            'type': 'objectid',
            'data_relation': {
                'resource': 'users',
                'field': '_id'
            }
        },
        'default': [],
        'readonly': True
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

        # TODO: make mandatory when implemented on client side
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

    app.on_insert_requests += onInsert
    app.on_inserted_requests += onInserted
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

# on_insert_requests
def onInsert(requests):
    ''' (list of dict) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for request in requests:
        _addDefaultDestination(request)

# on_inserted_requests
def onInserted(requests):
    ''' (list of dict) -> NoneType
    An Eve hook used after insertion.
    '''

    for request in requests:
        _matchCandidates(request)

        # remove this during production
        _matchAllCandidates(request)

        # currently just send all invites out rather than one by one
        # for testing
        _generateRequestInvites(request, invitesInBatch=100)

# helpers

def _matchCandidates(request):
    ''' (dict) -> NoneType
    Finds suitable candidates to offer requestInvites to based on their
    travel region and current location.
    '''

    # first, build the request's routes
    routes = []
    destination = app.data.driver.db['addresses'].find_one({
        '_id': request['destination']
    })

    for place in request['places']:
        routes += [{
            'type': 'LineString',
            'coordinates': [
                place['location']['coordinates'],
                destination['location']['coordinates']
            ]
        }]

    # then convert routes to a $geoIntersects with $or query
    intersects = [
        {
            'region': {
                '$geoIntersects': {
                    '$geometry': route
                }
            }
        }
        for route in routes
    ]

    # and then the full query (sorted by near the first place)
    # TODO: support multiple places, but this is a limitation of
    # MongoDB's $or operator
    query = {
        '$or': intersects,
        'location': {
            '$near': {
                '$geometry': request['places'][0]['location'],

            # TODO: add maxDistance.. but during development, don't
            # restrict to allow more candidates
            }
        },
        'current': True,

        # TODO: the cut off between hours will exclude those that haven't
        # reported this hour yet.. (which depends on the clients reporting
        # schedule; example: 15 minute reporting cycle will result in up to
        # first 15 minutes not being considered)

        # will definately cause less available deliveries during the start
        # of a hour

        # actually: we can just omit the hour, as long as the current
        # attribute is reliable
        #'hour': 
        'dayOfWeek': datetime.utcnow().isoweekday()
    }
    locationOfCandidates = app.data.driver.db['locations'].find(query)

    # now, filter out those candidates that aren't active
    candidates = []
    for location in locationOfCandidates:
        candidate = app.data.driver.db['users'].find_one({
            '_id': location['createdBy']
        })

        # prevent invites being sent out to the owner
        if candidate['active'] and candidate['_id'] != request['createdBy']:
            candidates.append(candidate['_id'])

    # append to the request
    request['candidates'] += candidates
    app.data.driver.db['requests'].update(
        {'_id': request['createdBy']},
        {'$set': {'candidates': request['candidates'] + candidates}},
        upsert=False, multi=False
    )

def _matchAllCandidates(request):
    ''' (dict) -> NoneType
    For development use: matches everyone as a candidate.
    '''

    users = app.data.driver.db['users'].find({})
    for user in users:
        if user['active']:
            request['candidates'].append(user['_id'])

    # now remove duplicates
    request['candidates'] = list(set(request['candidates']))

    # update Mongo
    app.data.driver.db['requests'].update(
        {'_id': request['createdBy']},
        {'$set': {'candidates': request['candidates']}},
        upsert=False, multi=False
    )

def _generateRequestInvites(request, invitesInBatch=1):
    ''' (dict) -> NoneType
    Generates and sends invitesInBatch number of requestInvites via GCM
    from the list of suitable candidates.

    REQ: _matchCandidates was performed in the past.
    '''

    invitesGenerated = []
    for i in range(min(invitesInBatch, len(request['candidates']))):
        candidate = app.data.driver.db['users'].find_one({
            '_id': request['candidates'].pop(0)
        })

        # only send active users invites
        if candidate['active']:

            # adding to list of inviteIds is dependant on
            # on_inserted_requestInvites to get _id
            resp = post_internal('requestInvites', {
                'requestId': request['_id'],
                'from': request['createdBy']
            })

            if resp[3] == 201:

                # set ownership of invite to invitee
                app.data.driver.db['requestInvites'].update(
                    {'_id': resp[0]['_id']},
                    {'$set': {'createdBy': candidate['_id']}},
                    upsert=False, multi=False
                )

                # get updated requestInvite
                requestInvite = app.data.driver.db['requestInvites'].find_one(
                    {'_id': resp[0]['_id']}
                )

                # add this invite to the parent request list
                invitesGenerated.append(requestInvite['_id'])

                # and finally, send gcm out
                gcmSend(candidate['deviceId'], {
                    'type': 'requestInvite',
                    'requestInvite': requestInvite['_id']
                })

    # update list of inviteIds and candidates in Mongo
    app.data.driver.db['requests'].update(
        {'_id': request['_id']},
        {'$set': {
            'inviteIds': request['inviteIds'] + invitesGenerated,
            'candidates': request['candidates']
        }},
        upsert=False, multi=False
    )

def _addDefaultDestination(request):
    ''' (dict) -> NoneType
    Adds the closest address known to the requester's current location
    if destination is not specified.
    '''

    if 'destination' not in request:
        currentLocation = app.data.driver.db['locations'].find_one(
            {'createdBy': request['createdBy']},
            sort=[('_id', DESCENDING)]
        )

        if currentLocation:
            closestAddress = app.data.driver.db['addresses'].find_one(
                {
                    'createdBy': request['createdBy'],
                    'location': {
                        '$near' : {
                            '$geometry': currentLocation['location']
                        }
                    },

                    # never use temporary addresses (instead, keep creating
                    # new ones)
                    'temporary': False
                }
            )

            # requester has a known address, so include it
            if closestAddress:
                request['destination'] = closestAddress['_id']

            # otherwise, create a temporary address based on the user's
            # current location
            else:
                resp = post_internal('addresses', {
                    'location': currentLocation['location']
                })

                if resp[3] == 201:

                    # set ownership of invite to invitee and temporary status
                    app.data.driver.db['addresses'].update(
                        {'_id': resp[0]['_id']},
                        {'$set': {
                            'createdBy': request['createdBy'],
                            'temporary': True
                        }},
                        upsert=False, multi=False
                    )

                    # alert owner that an address was created for them
                    user = app.data.driver.db['users'].find_one(
                        {'_id': request['createdBy']}
                    )

                    gcmSend(user['deviceId'], {
                        'type': 'addressCreated',
                        'addressCreated': resp[0]['_id']
                    })

                    # finally, set destination to temporary address
                    request['destination'] = resp[0]['_id']
