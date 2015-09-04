from models.orm import MongoORM

class User(MongoORM):
    ''' A representation of an User in Frrand.
    '''

    @staticmethod
    def fromObjectId(source, objectId):
        ''' (bson.ObjectId) -> User
        Creates a User directly from database with an ObjectId of objectId.
        '''

        return MongoORM.fromObjectId(source, objectId, User)

    def selfOwn(self):
        ''' (User) -> User
        Sets the owner of this User to itself. Generally used on creation
        of a new User in Mongo.
        '''

        self.set('createdBy', self.getId())
        return self