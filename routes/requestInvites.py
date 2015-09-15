from flask import current_app as app
from datetime import datetime
import errors.requestInvites

# default expiry time of each requestInvite until deletion in minutes
DEFAULT_EXPIRY = 15

schema = {
    'requestId': {
        'type': 'objectid',
        'readonly': True,
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        }
    },
    'from': {
        'type': 'objectid',
        'readonly': True,
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
    },

    # TODO: add to post_internal on creation
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
        },
        'readonly': True
    },
    'complete': {
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

    app.on_fetched_item_requestInvites += onFetchedItem
    app.on_fetched_resource_requestInvites += onFetched
    app.on_inserted_requestInvites += onInserted
    app.on_update_requestInvites += onUpdate
    app.on_updated_requestInvites += onUpdated
    app.on_delete_item_requestInvites += onDeleteItem

# hooks

# on_fetched_item_requestInvites
def onFetchedItem(invite, preventDisplay=True):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    request is mutated with new values.
    '''

    import models.requestInvites as requestInvites
    requestInvite = requestInvites.Invite(
        app.data.driver.db,
        requestInvites.Invite.collection,
        **invite
    )

    if not requestInvite.isExpired():
        invite.update(requestInvite.embedView())

    # prune and remove from list if expired
    else:
        _removeInvite(requestInvite)

        # prevent display
        del invite
        if preventDisplay: errors.requestInvites.abortInviteExpired()

# on_fetched_resource_requestInvites
def onFetched(invites):
    ''' (dict) -> NoneType
    An Eve hook used when fetching a list of requestInvites.
    '''

    if '_items' in invites:
        for invite in invites['_items']:
            onFetchedItem(invite, False)            

# on_inserted_requestInvites
def onInserted(invites):
    ''' (dict) -> NoneType
    An Eve hook used after insertion.
    '''

    import models.requestInvites as requestInvites
    for invite in invites:
        requestInvites.Invite(
            app.data.driver.db,
            requestInvites.Invite.collection,
            **invite
        ).addExpiry(DEFAULT_EXPIRY).commit()

# on_update_requestInvites
def onUpdate(changes, invite):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to update.
    '''

    import models.requestInvites as requestInvites
    requestInvite = requestInvites.Invite.fromObjectId(
        app.data.driver.db,
        invite['_id']
    )

    # disallow expired invites
    if requestInvite.isExpired():
        _removeInvite(requestInvite)
        errors.requestInvites.abortInviteExpired()

    # disallow changes once accepted (only way to refuse an invite is
    # to delete it)
    elif 'accepted' in changes and requestInvite.isAccepted():
        errors.requestInvites.abortImmutableAccepted()

    # invitee is posting feedback
    elif 'rating' in changes or 'comment' in changes:
        if not requestInvite.isComplete():
            errors.requestInvites.abortFeedBackUncompleted()
        elif requestInvite.feedbackSubmitted():
            errors.requestInvites.abortImmutableFeedback()

# on_updated_requestInvites
def onUpdated(changes, invite):
    ''' (dict, dict) -> NoneType
    An Eve hook used after update.
    '''

    import models.requestInvites as requestInvites
    requestInvite = requestInvites.Invite.fromObjectId(
        app.data.driver.db,
        invite['_id']
    )

    # notify requester of accept
    if 'accepted' in changes:
        requestInvite.accept()

    # post feedback from invitee
    if 'rating' in changes or 'comment' in changes:

        # create publicly viewable feedback
        import models.feedback as feedback
        feedback.Feedback.new(
            app.data.driver.db,
            requestInvite.getRequest(),
            False
        )

# on_delete_item_requestInvites
def onDeleteItem(invite):
    ''' (dict) -> NoneType
    An Eve hook used prior to an invite being deleted.
    '''

    # prevent deletion of attached invites
    import models.requestInvites as requestInvites
    requestInvite = requestInvites.Invite(
        app.data.driver.db,
        requestInvites.Invite.collection,
        **invite
    )

    # prevent deletion of attached invites
    if requestInvite.isAttached():
        errors.requestInvites.abortDeleteAttached()
    else:
        _removeInvite(requestInvite)

# helpers

def _removeInvite(invite):
    ''' (models.requestInvites.Invite) -> NoneType
    Removes the Invite from its Request.
    '''

    request = invite.getRequest()
    request.removeInvite(invite).commit()

    # in case invites have all expired
    import routes.requests as requestsRoute
    requestsRoute._refreshInvites(request)
