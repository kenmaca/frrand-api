import models.orm as orm

class Comment(orm.MongoORM):
    ''' A representation of Comment for Requests in Frrand.
    '''

    collection = 'comments'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Comment
        Creates Comment directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Comment)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Comment
        Finds a single Comment given query.
        '''

        return orm.MongoORM.findOne(db, Comment, **query)

    def setOwner(self, ownerId):
        ''' (Comment, ObjectId) -> Comment
        Sets the owner of this Comment to ownerId.
        '''

        self.set('createdBy', ownerId)
        return self

    def getOwner(self):
        ''' (Comment) -> models.users.User
        Gets the owner of this Comment.
        '''

        import models.users as users
        return users.User.fromObjectId(
            self.db,
            self.get('createdBy')
        )

    def getRequest(self):
        ''' (Comment) -> Request
        Gets the parent Request for this Comment.
        '''

        import models.requests as requests
        return requests.Request.fromObjectId(self.db, self.get('requestId'))
