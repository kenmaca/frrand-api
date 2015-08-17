import routes.users
import routes.apiKeys
import routes.locations
import routes.requests
import routes.requestInvites

# Eve
DEBUG = True

# Database
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
    'apiKeys': routes.apiKeys.config,
    'locations': routes.locations.config,
    'requests': routes.requests.config,
    'requestInvites': routes.requestInvites.config
}
