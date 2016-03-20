import models.orm as orm

class Group(orm.MongoORM):
    ''' A representation of a Group in Frrand.
    '''

    collection = 'groups'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Group
        Creates a Group directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Group)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Group
        Finds a single Group given query.
        '''

        return orm.MongoORM.findOne(db, Group, **query)

    @staticmethod
    def compat(user):
        ''' (User) -> User
        Provides compatibility support to users created before the implementation
        of Groups.
        '''

        return user.set('groups', []) if not user.exists('groups') else user
            
    def join(self, user):
        ''' (Group, User) -> Group
        Joins a User to this Group.
        '''

        Group.compat(user).pushUnique('groups', self.getId()).commit()
        return self

    def kick(self, user):
        ''' (Group, User) -> Group
        Removes the User user from this Group.
        '''

        Group.compat(user).listRemove('groups', self.getId()).commit()
        return self

    def contribute(self):
        ''' (Group) -> Group
        Increments this Group's delivery total.
        '''

        self.increment('deliveries')
        return self

    def isAuthorized(self, user):
        ''' (Group, User) -> bool
        Determines if the User user is a known administrator of this Group
        and can modify this Group's attributes.
        '''

        return user.getId() in self.get('admins')

    def authorize(self, user):
        ''' (Group, User) -> Group
        Adds the User user as an administrator of this Group.
        '''

        self.pushUnique('admins', user.getId())
        return self
