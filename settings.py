import routes.users
import routes.apiKeys
import routes.locations
import routes.requests
import routes.requestInvites

# Eve
DEBUG = True
API_NAME = 'Frrand API'
SERVER_NAME = 'api.frrand.com:5000'

# Database
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = 'frrand'
MONGO_PASSWORD = 'Triangular'
MONGO_DBNAME = 'frrand'

# Google Services
GCM_API_KEY = 'AIzaSyCvJlZQUf1fEEi0812f_-yNQptbra9IRts'

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
