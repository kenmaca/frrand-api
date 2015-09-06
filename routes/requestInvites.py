from flask import current_app as app
from flask import abort
from datetime import datetime
from models.requestInvites import Invite
from models.requests import Request
from models.users import User
from routes.requests import _refreshInvites

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
    'accepted': {
        'type': 'boolean',
        'default': False
    },
    'attached': {
        'type': 'boolean',
        'default': False,
        'readonly': True
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

    app.on_pre_GET_requestInvites += onPreGet
    app.on_fetched_item_requestInvites += onFetchedItem
    app.on_inserted_requestInvites += onInserted
    app.on_update_requestInvites += onUpdate
    app.on_updated_requestInvites += onUpdated
    app.on_deleted_item_requestInvites += onDeletedItem

# hooks

# on_pre_GET_requestInvites
def onPreGet(request, lookup):
    ''' (Request, dict) -> NoneType
    An Eve hook used to force a fresh fetch.
    '''

    if '_id' in lookup:

        # update last updated to trigger fresh fetch each time
        (Invite.fromObjectId(app.data.driver.db, lookup['_id'])
            .set('_updated': datetime.utcnow()).commit()
        )

# on_fetched_item_requestInvites
def onFetchedItem(invite):
    ''' (dict) -> NoneType
    An Eve hook used to embed requests to its child requestInvites as
    well as to convert all times to strings in RFC-1123 standard.
    request is mutated with new values.
    '''

    requestInvite = Invite(
        app.data.driver.db,
        Invite.collection,
        **invite
    )

    if not requestInvite.isExpired():
        invite.update(requestInvite.embedView())

    # prune and remove from list if expired
    else:
        _removeInvite(requestInvite)

        # prevent display
        abort(404)

# on_inserted_requestInvites
def onInserted(invites):
    ''' (dict) -> NoneType
    An Eve hook used after insertion.
    '''

    for invite in invites:
        Invite(
            app.data.driver.db,
            Invite.collection,
            **invite
        ).addExpiry(DEFAULT_EXPIRY).commit()

# on_update_requestInvites
def onUpdate(changes, invite):
    ''' (dict, dict) -> NoneType
    An Eve hook used prior to update.
    '''

    requestInvite = Invite.fromObjectId(app.data.driver.db, invite['_id'])

    # disallow expired invites
    if requestInvite.isExpired():
        _removeInvite(requestInvite)
        abort(422)

    # disallow changes once accepted (only way to refuse an invite is
    # to delete it)
    elif 'accepted' in changes and requestInvite.get('accepted'):
        abort(422)

# on_updated_requestInvites
def onUpdated(changes, invite):
    ''' (dict, dict) -> NoneType
    An Eve hook used after update.
    '''

    if 'accepted' in changes:
        Invite.fromObjectId(
            app.data.driver.db,
            invite['_id']
        ).accept().commit()

# on_deleted_item_requestInvites
def onDeletedItem(invite):
    ''' (dict) -> NoneType
    An Eve hook used after an item is deleted.
    '''

    (Request.fromObjectId(app.data.driver.db, invite['requestId'])
        .removeInvite(
            Invite(
                app.data.driver.db,
                Invite.collection,
                **invite
            )
        )
    )

# helpers

def _removeInvite(invite):
    ''' (models.requestInvites.Invite) -> NoneType
    Removes the Invite from its Request.
    '''

    request = Request.fromObjectId(
        app.data.driver.db,
        invite.get('requestId')
    ).removeInvite(invite).commit()

    # in case invites have all expired
    _refreshInvites(request)