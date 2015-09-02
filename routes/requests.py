from flask import current_app as app
from flask import abort
from eve.methods.post import post_internal
from eve.methods.delete import deleteitem_internal
from eve.methods.patch import patch_internal
from datetime import datetime
from pytz import UTC
from bson import ObjectId
from lib.gcm import gcmSend
from pymongo import DESCENDING
from routes.requestInvites import _isExpired

# number of invites to send at a time
BATCH_SIZE = 100

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
    'publicRequestInviteId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'publicRequestInvites',
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
    app.on_fetched_item_requests += onFetchedItem
    app.on_updated_requests += onUpdated

# hooks

# on_updated_requests
def onUpdated(updated, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used after an updated request.
    '''

    _removeInvites(updated, original)

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
def onFetchedItem(request):
    ''' (dict) -> NoneType
    An Eve hook used during fetching a request.
    '''

    _embedRequestDisplay(request)

def _embedRequestDisplay(request):
    ''' (dict) -> NoneType
    Embeds requestInvites to its parent request for display.
    '''

    pendingInvites = []
    pendingInviteIds = []
    if 'inviteIds' in request:
        for inviteId in request['inviteIds']:
            requestInvite = app.data.driver.db['requestInvites'].find_one({
                '_id': inviteId
            })

            if not _isExpired(requestInvite):
                pendingInvites.append(requestInvite)
                pendingInviteIds.append(requestInvite['_id'])

        # prune expired invites if the inviteIds list changed
        if pendingInviteIds != request['inviteIds']:
            patch_internal('requests',
                {'inviteIds': pendingInviteIds},
                _id=request['_id']
            )

            # update publicRequestInviteId if the request was converted
            publicInvite = app.data.driver.db['publicRequestInvites'].find_one(
                {'requestId': request['_id']}
            )

            if publicInvite:
                request['publicRequestInviteId'] = publicInvite['_id']

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
        _generateRequestInvites(request, BATCH_SIZE)

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

        # TODO: possible bug, if current batch contains no sendable
        # invites, then request is hanging around without invites

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

def _refreshInvites(request):
    ''' (dict) -> NoneType
    Generates new requestInvites if the list is empty and there are
    still candidates. Generates a publicRequestInvite if there are
    no requestInvites and no more candidates.
    '''

    if not request['inviteIds']:
        if request['candidates']:
            _generateRequestInvites(request)

        # unclaimed, so create a publicRequestInvite if one doesn't
        # already exist
        elif not request['publicRequestInviteId']:

            # get a fresh copy since provided one doesn't supply
            # createdBy
            request = app.data.driver.db['requests'].find_one({
                '_id': request['_id']
            })
            resp = post_internal(
                'publicRequestInvites', {
                    'requestId': request['_id'],
                    'from': request['createdBy']
                }
            )

            if resp[3] == 201:
                app.data.driver.db['requests'].update(
                    {'_id': request['_id']},
                    {'$set': {
                        'publicRequestInviteId': resp[0]['_id']
                    }},
                    upsert=False, multi=False
                )

def _removeInvites(updated, original):
    ''' (dict, dict) -> NoneType
    Removes any invites from Mongo that don't appear in the
    updated copy but do in the original.
    '''

    if 'inviteIds' in updated:
        for invite in original['inviteIds']:
            if invite not in updated['inviteIds']:

                # TODO: fix hacky direct deletion. should be using
                # eve.methods.delete.deleteitem_internal instead
                # to trigger any hooks, but should be safe here
                # since no hooks need to be called after removing
                # both from the parent request inviteIds list and
                # the requestInvite itself.
                # deleteitem_internal appears to not work when
                # called within another internal call?
                app.data.driver.db['requestInvites'].remove({
                    '_id': invite
                })

        # pump out more invites if the invite list is empty
        original['inviteIds'] = updated['inviteIds']
        _refreshInvites((lambda a, b: a.update(b) or a)(
           original,
           updated
        ))
