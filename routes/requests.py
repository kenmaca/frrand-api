from flask import current_app as app
from flask import abort
from eve.methods.post import post_internal
from datetime import datetime

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
        'default': None,
        'readonly': True
    },
    'destination': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'addresses',
            'field': '_id'
        },

        # TODO: make mandatory when implemented on client side
    },
    'complete': {
        'type': 'boolean',
        'default': False
    },
    'rating': {
        'type': 'integer',
        'min': 1,
        'max': 5,
        'dependencies': [
            'complete'
        ]
    },
    'comment': {
        'type': 'string',
        'maxlength': 240
        'dependencies': [
            'complete',
            'rating'
        ]
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
    app.on_fetched_item_requests += onFetchedItem
    app.on_fetched_resource_requests += onFetched
    app.on_update_requests += onUpdate

# hooks

# on_update_requests
def onUpdate(updated, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to an update.
    '''

    import models.requests as requests
    request = requests.Request.fromObjectId(
        app.data.driver.db,
        original['_id']
    ).update(updated)

    # inviteIds have changed
    if 'inviteIds' in updated:
        if request.getOriginal('attachedInviteId'):
            abort(422, 'Cannot change Invites once attached')
        else:
            _removeInvites(request)

    # owner has attached an invite
    if 'attachedInviteId' in updated:
        if request.getOriginal('attachedInviteId'):
            abort(422, 'Already attached')
        else:
            try:
                invite = request.getAttached()
                request.attachInvite(invite)
                invite.commit()
            except ValueError:
                abort(422, 'Unable to attach Invite')

    # owner has confirmed completion of this Request
    if 'complete' in updated:
        if request.getOriginal('complete'):
            abort(422, 'Already complete')

        # use getOriginal to disallow attaching and completing in one step
        elif not request.getOriginal('attached'):
            abort(422, 'Cannot complete an unattached Request')
        else:

            # set to completed
            request.complete().commit()

    # owner is posting feedback
    if 'rating' in updated or 'comment' in updated:
        if not request.isComplete():
            abort(422, 'Cannot submit feedback for uncompleted Request')
        elif request.feedbackSubmitted():
            abort(422, 'Cannot alter existing feedback')
        else:

            # create publicly viewable feedback
            import models.feedback as feedback
            feedback.Feedback.new(
                app.data.driver.db,
                request,
                True
            )

# on_fetched_item_requests
def onFetchedItem(fetchedRequest):
    ''' (dict) -> NoneType
    An Eve hook used during fetching a request.
    '''

    import models.requests as requests
    request = requests.Request.fromObjectId(
        app.data.driver.db,
        fetchedRequest['_id']
    )

    # prune expired before presenting and refresh
    if not request.isAttached():
        _refreshInvites(request.pruneExpiredInvites())
        
    fetchedRequest.update(request.commit().embedView())

def onFetched(fetchedRequests):
    ''' (dict) -> NoneType
    An Eve hook used during fetching a list of requests.
    '''

    # embed each request
    if '_items' in fetchedRequests:
        for request in fetchedRequests['_items']:
            onFetchedItem(request)

# on_insert_requests
def onInsert(insertedRequests):
    ''' (list of dict) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for request in insertedRequests:
        if 'complete' in request and request['complete']:
            abort(422, 'Cannot set completion on Request creation')

# on_inserted_requests
def onInserted(insertedRequests):
    ''' (list of dict) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.requests as requests
    for request in insertedRequests:
        request = requests.Request(
            app.data.driver.db,
            requests.Request.collection,
            **request
        )

        _addDefaultDestination(request)
        request.matchOwnerAsCandidate()
        _refreshInvites(request)
        request.commit()        

# helpers

def _generateRequestInvites(request, invitesInBatch=1):
    ''' (models.requests.Request, int) -> NoneType
    Generates and sends invitesInBatch number of requestInvites via GCM
    from the list of suitable candidates.
    '''

    import models.users as users
    import models.requestInvites as requestInvites
    for i in range(min(invitesInBatch, len(request.get('candidates')))):
        candidate = users.User.fromObjectId(
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
                invite = requestInvites.Invite.fromObjectId(
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
        import models.addresses as addresses

        user = request.getOwner()
        currentLocation = user.getLastLocation()

        if currentLocation:
            try:
                address = addresses.Address.findOne(
                    app.data.driver.db,
                    **{
                        'createdBy': user.getId(),
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
                        addresses.Address.fromObjectId(
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
        else:
            request.remove()
            abort(422, 'No location history exists')

def _refreshInvites(request):
    ''' (models.requests.Request) -> NoneType
    Generates new requestInvites if the list is empty and there are
    still candidates. Generates a publicRequestInvite if there are
    no requestInvites and no more candidates.
    '''

    # prevent generating anymore invites once attached
    if not request.isAttached():
        if not request.get('inviteIds'):
            if request.get('candidates'):
                _generateRequestInvites(request, BATCH_SIZE)

            # unclaimed, so create a publicRequestInvite if one doesn't
            # already exist
            elif not request.isPublic():
                resp = post_internal(
                    'publicRequestInvites', {
                        'requestId': request.getId(),
                        'from': request.get('createdBy')
                    }
                )

                if resp[3] == 201:
                    request.set(
                        'publicRequestInviteId', resp[0]['_id']
                    ).commit()

def _removeInvites(request):
    ''' (models.requests.Request) -> NoneType
    Removes any invites from Mongo that don't appear in the
    updated copy but do in the original.
    '''

    import models.requestInvites as requestInvites
    for invite in request.getOriginal('inviteIds'):
        if invite not in request.get('inviteIds'):
            request.removeInvite(
                requestInvites.Invite.fromObjectId(
                    app.data.driver.db,
                    invite
                )
            )

    # pump out more invites if the inviteIds list is empty    
    _refreshInvites(request.commit())
