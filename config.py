# Eve
DEBUG = True
API_NAME = 'Frrand API'
SERVER_NAME = 'data.frrand.com'
CACHE_CONTROL = 'max-age=0,must-revalidate'
MEDIA_BASE_URL = 'http://%s' % SERVER_NAME
RETURN_MEDIA_AS_URL = True
RETURN_MEDIA_AS_BASE64_STRING = False

# Database
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = ''
MONGO_PASSWORD = ''
MONGO_DBNAME = 'frrand'

# Security
AUTH_FIELD = 'createdBy'
PUBLIC_METHODS = []
PUBLIC_ITEM_METHODS = []

# Google
GCM_API_KEY = 'AIzaSyCvJlZQUf1fEEi0812f_-yNQptbra9IRts'

# SMS
SMS_API_KEY = 'o5I3co86Kn4wi43MZhpK6wtS027D445y'
