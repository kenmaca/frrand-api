import routes.users
import routes.addresses
import routes.apiKeys
import routes.locations
import routes.requests
import routes.requestInvites
import routes.publicRequestInvites
import routes.feedback
import routes.comments
import routes.profiles
from config import *

# Routes
DOMAIN = {
    'users': routes.users.config,
    'addresses': routes.addresses.config,
    'apiKeys': routes.apiKeys.config,
    'locations': routes.locations.config,
    'requests': routes.requests.config,
    'requestInvites': routes.requestInvites.config,
    'publicRequestInvites': routes.publicRequestInvites.config,
    'feedback': routes.feedback.config,
    'comments': routes.comments.config,
    'profiles': routes.profiles.config
}

# Utils
def init(app):
    ''' (LocalProxy) -> NoneType
    Adds all known hooks to their respective routes as defined by
    each route's init function.
    '''

    routes.users.init(app)
    routes.addresses.init(app)
    routes.apiKeys.init(app)
    routes.locations.init(app)
    routes.requests.init(app)
    routes.requestInvites.init(app)
    routes.publicRequestInvites.init(app)
    routes.feedback.init(app)
    routes.comments.init(app)
