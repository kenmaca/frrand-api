import routes.users
import routes.locations
import routes.apiKeys

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
    'locations': routes.locations.config
}
