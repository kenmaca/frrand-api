from flask import current_app as app
from datetime import datetime
import errors.requestInvites

# default expiry time of each requestInvite until deletion in minutes
DEFAULT_EXPIRY = 5

schema = {
    'requestId': {
        'type': 'objectid',
        'readonly': True,
        'data_relation': {
            'resource': 'requests',
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
    'cancel': {
        'type': 'boolean',
        'default': False
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

        # refuse if comment previously exists, or if rating is being changed
        elif (
            requestInvite.feedbackSubmitted()
            and requestInvite.getFeedback().get('comment')
        ) or (
            requestInvite.feedbackSubmitted()
            and 'rating' in changes
        ):
            errors.requestInvites.abortImmutableFeedback()

    # prevent enabling mutually cancelled requests
    elif 'cancel' in changes and requestInvite.getRequest().isMutuallyCancelled():
        errors.requestInvites.abortImmutableMutuallyCancelled()

    # prevent cancellation of completed
    elif 'cancel' in changes and requestInvite.isComplete():
        errors.requestInvites.abortAlreadyCancelled()

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

    # remove invite completely if invite is now expired
    if requestInvite.isExpired():
        _removeInvite(requestInvite)
    else:

        # trigger request mutual cancellation process
        if 'cancel' in changes:
            requestInvite.getRequest().requestCancellation().commit()

        # notify requester of accept
        if 'accepted' in changes:
            requestInvite.accept()

        # post feedback from deliverer
        if 'rating' in changes:
            import models.feedback as feedback
            feedback.Feedback.new(
                app.data.driver.db,
                requestInvite.getRequest(),
                False
            )

        # feedback exists, so just modify comment
        elif 'comment' in changes:
            requestInvite.getFeedback().set(
                'comment',
                changes['comment']
            ).commit()

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
