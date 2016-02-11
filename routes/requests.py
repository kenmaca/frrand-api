from flask import current_app as app, g
from eve.methods.post import post_internal
from datetime import datetime
import errors.requests
import messages.requests

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
        'required': True
    },
    'complete': {
        'type': 'boolean',
        'default': False
    },
    'pickedUp': {
        'type': 'boolean',
        'default': False,
        'readonly': True
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
        'maxlength': 240,
        'dependencies': [
            'complete',
            'rating'
        ]
    },
    'points': {
        'type': 'integer',
        'min': 1,
        'default': 1
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
    app.on_updated_requests += onUpdated

# hooks

# on_update_requests
def onUpdate(updated, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to an update.
    '''

    import models.requests as requests
    originalRequest = requests.Request.fromObjectId(
        app.data.driver.db,
        original['_id']
    )
    request = requests.Request.fromObjectId(
        app.data.driver.db,
        original['_id']
    ).update(updated)

    # prevent change of points awarded
    if 'points' in updated:
        errors.requests.abortImmutablePoints()

    # inviteIds have changed
    if 'inviteIds' in updated:
        if originalRequest.isAttached():
            errors.requests.abortImmutableInvitesOnAttached()
        else:
            _removeInvites(request)

    # owner has attached an invite
    if 'attachedInviteId' in updated:
        import models.requestInvites as invites
        try:

            # only allow attach if the invite exists
            invites.Invite.fromObjectId(app.data.driver.db, updated['attachedInviteId'])

            if originalRequest.isAttached():
                errors.requests.abortAlreadyAttached()
            else:
                try:
                    invite = request.getAttached()
                    request.attachInvite(invite).commit()
                    invite.commit()
                except ValueError:
                    errors.requests.abortAttachInvite()
        except KeyError:
            errors.requests.abortExpiredInvite()

    # owner has confirmed completion of this Request
    if 'complete' in updated:
        if originalRequest.isComplete():
            errors.requests.abortComplete()

        # use original to disallow attaching and completing in one step
        elif not originalRequest.isAttached():
            errors.requests.abortCompleteUnattached()
        else:

            # set to completed
            request.complete().commit()

    # owner is posting feedback
    if 'rating' in updated or 'comment' in updated:
        if not request.isComplete():
            errors.requests.abortFeedBackUncompleted()

        # refuse if comment previously exists, or if rating is being changed
        elif (
            originalRequest.feedbackSubmitted()
            and originalRequest.getFeedback().get('comment')
        ) or (
            originalRequest.feedbackSubmitted()
            and 'rating' in updated
        ):
            errors.requests.abortImmutableFeedback()

# on_updated_requests
def onUpdated(changes, original):
    ''' (dict, dict) -> NoneType
    An Eve hook used after update.
    '''

    import models.requests as requests
    request = requests.Request.fromObjectId(
        app.data.driver.db,
        original['_id']
    )

    # post feedback from requester
    if 'rating' in changes:
        import models.feedback as feedback
        feedback.Feedback.new(
            app.data.driver.db,
            request,
            True
        )

    # feedback exists, so just modify comment
    elif 'comment' in changes:
        request.getFeedback().set(
            'comment',
            changes['comment']
        ).commit()

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
            errors.requests.abortCompleteCreation()
        elif 'points' in request:
            import models.users as users
            if request['points'] > users.User.fromObjectId(
                app.data.driver.db,
                g.get('auth_value')
            ).get('points'):
                errors.requests.abortInsufficientPoints()

# on_inserted_requests
def onInserted(insertedRequests):
    ''' (list of dict) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.requests as requests
    for request in insertedRequests:
        if 'createdBy' in request:
            request = requests.Request(
                app.data.driver.db,
                requests.Request.collection,
                **request
            )

            request.matchCandidates()
            _refreshInvites(request)

            # keep aside points for awarding
            request.getOwner().stashPoints(request.getPoints()).commit()
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

            # create a stub invite to fill in internally (for security)
            resp = post_internal('requestInvites', {})
            if resp[3] == 201:

                # set ownership of invite to invitee
                invite = (
                    requestInvites.Invite.fromObjectId(
                        app.data.driver.db,
                        resp[0]['_id']
                    ).set('createdBy', candidate.getId())
                    .set('requestId', request.getId())
                    .commit()
                )

                # add this invite to the parent request list
                request.addInvite(invite).commit()

                # and finally, send gcm out
                candidate.message(*messages.requests.newInvite(invite.getId()))

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
                        'requestId': request.getId()
                    }
                )

                if resp[3] == 201:
                    import models.publicRequestInvites as publicInvites

                    request.set(
                        'publicRequestInviteId', resp[0]['_id']
                    ).commit()

                    public = publicInvites.PublicInvite.fromObjectId(
                        app.data.driver.db,
                        resp[0]['_id']
                    )

                    public.set(
                        'location',
                        public.getRequest().getDestination().getGeo()
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
