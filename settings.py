import routes.users
import routes.locations

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
    'locations': routes.locations.config
}
