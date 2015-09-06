from flask import current_app as app
from flask import abort
from eve.methods.post import post_internal
from datetime import datetime
from models.addresses import Address
from models.locations import location
from models.users import User
from models.requests import Request
from models.requestInvites import Invite

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

    app.on_inserted_requests += onInserted
    app.on_pre_GET_requests += onPreGet
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
def onPreGet(request, lookup):
    ''' (flask.Request, dict) -> NoneType
    An Eve hook used to force a fresh fetch.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        (Request.fromObjectId(app.data.driver.db, lookup['_id'])
            .set('_updated': datetime.utcnow()).commit()
        )

# on_fetched_item_requests
def onFetchedItem(request):
    ''' (dict) -> NoneType
    An Eve hook used during fetching a request.
    '''

    request.update(
        Request(
            app.data.driver.db,
            Request.collection,
            **request
        ).embedView()
    )

# on_inserted_requests
def onInserted(requests):
    ''' (list of dict) -> NoneType
    An Eve hook used after insertion.
    '''

    for request in requests:
        request = Request(
            app.data.driver.db,
            Request.collection,
            **request
        )

        _addDefaultDestination(request)
        _generateRequestInvites(request.matchAllCandidates(), BATCH_SIZE)

# helpers

def _generateRequestInvites(request, invitesInBatch=1):
    ''' (models.requests.Request, int) -> NoneType
    Generates and sends invitesInBatch number of requestInvites via GCM
    from the list of suitable candidates.
    '''

    for i in range(min(invitesInBatch, len(request.get('candidates')))):
        candidate = User.fromObjectId(
            app.data.driver.db,
            request.pop('candidates')
        )

        # TODO: possible bug, if current batch contains no sendable
        # invites, then request is hanging around without invites

        # only send active users invites
        if candidate.isActive():

            # adding to list of inviteIds is dependant on
            # on_inserted_requestInvites to get _id
            resp = post_internal('requestInvites', {
                'requestId': request.getId(),
                'from': request.get('createdBy')
            })

            if resp[3] == 201:

                # set ownership of invite to invitee
                invite = Invite.fromObjectId(
                    app.data.driver.db,
                    resp[0]['_id']
                ).set('createdBy', candidate.getId()).commit()

                # add this invite to the parent request list
                request.addInvite(invite).commit()

                # and finally, send gcm out
                candidate.message('requestInvite', invite.getId())

def _addDefaultDestination(request):
    ''' (models.requests.Request) -> NoneType
    Adds the closest address known to the requester's current location
    if destination is not specified.
    '''

    if not request.exists('destination'):
        user = User.fromObjectId(app.data.driver.db, request.get('createdBy'))
        currentLocation = user.getLastLocation()

        if currentLocation:
            try:
                address = Address.findOne(
                    app.data.driver.db,
                    {
                        'createdBy': request.get('createdBy'),
                        'location': {
                            '$near' : {
                                '$geometry': currentLocation.get('location')
                            }
                        },

                        # never use temporary addresses (instead, keep creating
                        # new ones)
                        'temporary': False
                    }
                )

            # otherwise, create a temporary address based on the user's
            # current location
            except KeyError:
                resp = post_internal('addresses', {
                    'location': currentLocation.get('location')
                })

                if resp[3] == 201:

                    # set ownership of invite to invitee and temporary status
                    address = (
                        Address.fromObjectId(
                            app.data.driver.db,
                            resp[0]['_id']
                        ).set('createdBy', user.getId())
                        .set('temporary', True)
                    ).commit()

                    # alert owner that an address was created for them
                    user.message('addressCreated', address.getId())

            # finally, set destination to either closest or temp address
            request.set('destination', address.getId())

        # do not allow creation of Request if no location data at all
        request.remove()
        abort(422)

def _refreshInvites(request):
    ''' (models.requests.Request) -> NoneType
    Generates new requestInvites if the list is empty and there are
    still candidates. Generates a publicRequestInvite if there are
    no requestInvites and no more candidates.
    '''

    if not request.get('inviteIds'):
        if request.get('candidates'):
            _generateRequestInvites(request, BATCH_SIZE)

        # unclaimed, so create a publicRequestInvite if one doesn't
        # already exist
        elif not request.get('publicRequestInviteId'):
            resp = post_internal(
                'publicRequestInvites', {
                    'requestId': request.getId(),
                    'from': request.get('createdBy')
                }
            )

            if resp[3] == 201:
                request.set('publicRequestInviteId', resp[0]['_id']).commit()

def _removeInvites(updated, original):
    ''' (dict, dict) -> NoneType
    Removes any invites from Mongo that don't appear in the
    updated copy but do in the original.
    '''

    request = Request.fromObjectId(
        app.data.driver.db,
        original['_id']
    ).update(updated)

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
                request.removeInvite(
                    Invite.fromObjectId(app.data.driver.db, invite)
                )

    # pump out more invites if the inviteIds list is empty    
    _refreshInvites(request.commit())