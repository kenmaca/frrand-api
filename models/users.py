import models.orm as orm
import lib.gcm as gcm
import lib.sms as sms
import bcrypt
import random
import re
from pymongo import DESCENDING

BCRYPT_ROUNDS = 8
BCRYPT_ENCODING = 'utf-8'
GEN_NOUNS = '/home/ec2-user/frrand/lib/nouns'
GEN_ADJS = '/home/ec2-user/frrand/lib/adjectives'

class User(orm.MongoORM):
    ''' A representation of an User in Frrand.
    '''

    collection = 'users'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> User
        Creates a User directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, User)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> User
        Finds a single User given query.
        '''

        return orm.MongoORM.findOne(db, User, **query)

    def selfOwn(self):
        ''' (User) -> User
        Sets the owner of this User to itself. Generally used on creation
        of a new User in Mongo.
        '''

        self.set('createdBy', self.getId())
        return self

    def getAddresses(self, temporary=False):
        ''' (User, bool) -> list of models.addresses.Address
        Obtains a listing of Addresses owned by this User.
        '''

        import models.addresses as addresses
        return [addresses.Address(
                self.db,
                addresses.Address.collection,
                **address
            ) for address in 
            self.db[addresses.Address.collection].find(
                {
                    'createdBy': self.getId(),
                    'temporary': temporary
                }
            )
        ]

    def getRequests(self, completed=False):
        ''' (User, bool) -> list of models.requests.Request
        Obtains a listing of Requests made by this User.
        '''

        import models.requests as requests
        return [requests.Request(
                self.db,
                requests.Request.collection,
                **request
            ) for request in
            self.db[requests.Request.collection].find(
                {
                    'createdBy': self.getId(),
                    'complete': completed
                }
            )
        ]

    def getInvites(self, completed=False):
        ''' (User, bool) -> list of models.requestInvites.Invite 
        Obtains a listing of Invites owned by this User.
        '''

        import models.requestInvites as invites
        return [invites.Invite(
                self.db,
                invites.Invite.collection,
                **invite
            ) for invite in
            self.db[invites.Invite.collection].find(
                {
                    'createdBy': self.getId(),
                    'complete': completed
                }
            )
        ]

    def message(self, messageType, message, deviceId=False):
        ''' (User, str, object) -> bool
        Sends a message to the last known device via GCM, or else
        deviceId if provided.
        '''

        if deviceId:
            return gcm.gcmSend(
                deviceId if deviceId else self.get('deviceId'),
                {
                    'type': messageType,
                    messageType: message
                }
            )

        # sends to all known devices for dev use
        else:
            return any([
                gcm.gcmSend(
                    apiKey.get('deviceId'),
                    {
                        'type': messageType,
                        messageType: message
                    }
                ) for apiKey in self.getApiKeys()
            ])

    def sms(self, message):
        ''' (User, str) -> bool
        Sends a SMS message to the user's phone number.
        '''

        if self.exists('phone'):
            return sms.smsSend(self.get('phone'), message)
        else:
            return False

    def getApiKeys(self):
        ''' (User) -> list of models.apiKeys.APIKey
        Gets all APIKeys owned by this User.
        '''

        keys = []
        import models.apiKeys as apiKeys
        for apiKey in self.source.find({'createdBy': self.getId()}):
            keys.append(
                apiKeys.APIKey(
                    self.db,
                    apiKeys.APIKey.collection,
                    **apiKey
                )
            )

        return keys

    def useApiKey(self, apiKey):
        ''' (User, models.apikeys.APIKey) -> User
        Updates the last known deviceId for this User.
        '''

        self.set('deviceId', apiKey.get('deviceId'))
        return self

    def isActive(self):
        ''' (User) -> bool
        Determines whether or not this User is accepting request invites.
        '''

        return self.get('active')

    def getLastLocation(self):
        ''' (User) -> models.locations.Location
        Gets the last reported Location for this User.
        '''

        try:
            import models.locations as locations
            return locations.Location.findOne(
                self.db,
                createdBy=self.getId()
            )
        except KeyError:
            return

    def getRating(self):
        ''' (User) -> int
        Gets the average rating for this User.
        '''

        return self.get('rating')

    def addRating(self, rating):
        ''' (User, int) -> User
        Adds a rating (1-5) to this User.
        '''

        self.set(
            'rating',
            (
                self.getRating()
                + (
                    (rating - self.getRating())
                    / (self.get('numberOfRatings') + 1)
                )
            )
        )
        self.increment('numberOfRatings')
        return self

    def awardPoints(self, points=1):
        ''' (User, int) -> User
        Adds points to this User's points.
        '''

        self.increment('points', points)
        return self

    def spendPoints(self, points=1):
        ''' (User, int) -> User
        Spends points from pendingPoints.
        '''

        self.increment('pendingPoints', -points)
        return self

    def stashPoints(self, points=1):
        ''' (User, int) -> User
        Stashes points from points into pendingPoints.
        '''

        (self
            .increment('points', -points)
            .increment('pendingPoints', points)
        )
        return self

    def authenticate(self, password):
        ''' (User, str) -> bool
        Determines whether or not the plain-text password matches the
        password stored in this User.
        '''

        return (
            bcrypt.hashpw(
                password.encode(BCRYPT_ENCODING),
                self.get('salt').encode(BCRYPT_ENCODING)
            )
            == self.get('password')
        )

    def setPassword(self, password):
        ''' (User, str) -> User
        Encrypts the given plain-text password and securely stores it in
        this User.
        '''

        self.set('salt', bcrypt.gensalt(BCRYPT_ROUNDS))
        self.set(
            'password', 
            bcrypt.hashpw(
                password.encode(BCRYPT_ENCODING),
                self.get('salt').encode(BCRYPT_ENCODING)
            )
        )
        return self

    def changePhoneNumber(self, phone):
        ''' (User, str) -> User
        Changes this User's phone number.
        '''

        self.set('phone', phone)
        self.setVerificationCode()
        return self

    def setVerificationCode(self):
        ''' (User) -> User
        Sets a verification code for this User's phone number.
        '''

        self.set('phoneVerified', False)
        self.set('_verificationCode', str(random.randint(100000, 999999)))
        
        # active sending disabled until terence stops wasting my money
        self.sms(
            'Your Frrand Verification Code is: %s'
            % self.get('_verificationCode')
        )
        return self

    def verifyPhone(self):
        ''' (User) -> User
        Verifies this user's phone number if verificationCode matches 
        _verificationCode.
        '''

        if self.get('verificationCode') == self.get('_verificationCode'):
            self.set('phoneVerified', True)
            self.set('verificationCode', None)
            self.message(
                'phoneVerified',
                self.get('phone')
            )
        return self

    @staticmethod
    def generateUsername(db, min=2, max=2):
        ''' (pymongo.database.Database, str) -> User
        Sets the username of this User to name if name is provided, otherwise
        generates a random username to assign this User to.
        '''

        # build word lists
        with open(GEN_NOUNS) as n:
            nouns = n.read().splitlines()
        with open(GEN_ADJS) as a:
            adjs = a.read().splitlines()

        while True:
            username = '-'.join(
                [re.sub(r'\W+', '', random.choice(adjs)) for i in range(
                    random.randint(min, max) - 1
                )]
                + [
                    re.sub(r'\W+', '', random.choice(nouns))
                    + str(random.randint(1,999))
                ]
            )

            # test if username is valid
            try:
                User.findOne(db, username=username)

            # doesn't exist, good to go
            except KeyError:
                return username

# helpers

def getCurrentUser(db):
    ''' (pymongo.database.Database) -> User
    Gets the User currently logged in.
    '''

    from flask import g
    userId = g.get('auth_value')
    if userId:
        try:
            return User.fromObjectId(
                db,
                userId
            )
        except KeyError:
            return
