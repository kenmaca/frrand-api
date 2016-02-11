from flask import current_app as app, g
from utils.auth import FacebookAuth
from routes.apiKeys import _provision, onInserted
import errors.fbApiKeys
from facebook import GraphAPI, GraphAPIError

config = {
    'item_title': 'fbApiKeys',
    'public_methods': [],
    'public_item_methods': [],
    'datasource': {
        'source': 'apiKeys'
        }
    },
    'allowed_filters': [],
    'item_methods': [],
    'resource_methods': ['POST'],
    'authentication': FacebookAuth()
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_insert_fbApiKeys += onInsert
    app.on_inserted_fbApiKeys += onInserted

# hooks

# on_insert_apiKeys
def onInsert(insertApiKeys):
    ''' (list of dicts) -> NoneType
    An Eve hook used prior to insertion.
    '''

    for apiKey in insertApiKeys:
        try:

            # ensure that the user actually has access to the
            # facebook account
            fb = GraphAPI(apiKey['facebookToken'], version='2.2')
            import models.users as users
            user = users.User.findOne(
                app.data.driver.db,
                facebookId=fb.get_object('me')['id']
            )
            if g.get('auth_value') != user.getId():
                raise KeyError()

            # otherwise, allow it
            _provision(apiKey)
        except (GraphAPIError, KeyError):
            errors.fbApiKeys.abortInvalidFacebookToken()
