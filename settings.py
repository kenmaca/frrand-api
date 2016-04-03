import routes.users
import routes.addresses
import routes.apiKeys
import routes.fbApiKeys
import routes.locations
import routes.requests
import routes.requestInvites
import routes.publicRequestInvites
import routes.feedback
import routes.comments
import routes.mirrors.profiles
import routes.vouchers
import routes.mirrors.adminUsers
import routes.mirrors.adminApiKeys
import routes.mirrors.adminRequests
import routes.groups
import routes.redeem
from config import *

# Routes
DOMAIN = {
    'users': routes.users.config,
    'addresses': routes.addresses.config,
    'apiKeys': routes.apiKeys.config,
    'fbApiKeys': routes.fbApiKeys.config,
    'locations': routes.locations.config,
    'requests': routes.requests.config,
    'requestInvites': routes.requestInvites.config,
    'publicRequestInvites': routes.publicRequestInvites.config,
    'feedback': routes.feedback.config,
    'comments': routes.comments.config,
    'profiles': routes.mirrors.profiles.config,
    'vouchers': routes.vouchers.config,
    'adminUsers': routes.mirrors.adminUsers.config,
    'adminRequests': routes.mirrors.adminRequests.config,
    'adminApiKeys': routes.mirrors.adminApiKeys.config,
    'groups': routes.groups.config,
    'redeem': routes.redeem.config
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
    routes.fbApiKeys.init(app)
    routes.locations.init(app)
    routes.requests.init(app)
    routes.requestInvites.init(app)
    routes.publicRequestInvites.init(app)
    routes.feedback.init(app)
    routes.comments.init(app)
    routes.mirrors.profiles.init(app)
    routes.vouchers.init(app)
    routes.mirrors.adminUsers.init(app)
    routes.mirrors.adminRequests.init(app)
    routes.mirrors.adminApiKeys.init(app)
    routes.groups.init(app)
    routes.redeem.init(app)
