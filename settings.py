import routes.users
import routes.addresses
import routes.apiKeys
import routes.locations
import routes.requests
import routes.requestInvites

# Eve
DEBUG = True
API_NAME = 'Frrand API'
SERVER_NAME = 'api.frrand.com:5000'
CACHE_CONTROL = 'max-age=0,must-revalidate'

# Database
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = 'frrand'
MONGO_PASSWORD = 'Triangular'
MONGO_DBNAME = 'frrand'

# Security
AUTH_FIELD = 'createdBy'
PUBLIC_METHODS = []
PUBLIC_ITEM_METHODS = []

# Routes
DOMAIN = {
    'users': routes.users.config,
    'addresses': routes.addresses.config,
    'apiKeys': routes.apiKeys.config,
    'locations': routes.locations.config,
    'requests': routes.requests.config,
    'requestInvites': routes.requestInvites.config
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
