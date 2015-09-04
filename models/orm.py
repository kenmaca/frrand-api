from copy import deepcopy

class MongoORM:
    ''' A Object-Relational Model to a document in MongoDB.
    '''

    def __init__(self, source, **fields):
        ''' (MongoORM, pymongo.collection.Collection) -> MongoORM
        Produces a MongoORM from key-value pairs in fields existing in the 
        Collection source in a MongoDB database.
        '''

        # require all MongoORMs have _ids
        if '_id' not in fields:
            raise ValueError('Missing ObjectId')

        self.source, self._original = source, fields
        self.reset()

    @staticmethod
    def fromObjectId(source, objectId, resultantClass):
        ''' (pymongo.collection.Collection, bson.ObjectId, MongoORM) -> MongoORM
        Creates a MongoORM directly from the Mongo collection in source with
        the ObjectId of objectId in the resultantClass.
        '''

        objectData = source.find_one({'_id': objectId})
        if objectData:
            return resultantClass(source, **objectData)

        # non-existant objectId
        raise KeyError('%s does not exist in %s' % (
            str(objectId), str(source)
        ))

    def reset(self, forward=False):
        ''' (MongoORM) -> MongoORM
        Sets the both states of this MongoORM to the current state if forward
        is True, otherwise back to the original state.
        '''

        if forward:
            self._original.update(self._current)
        self._current = {}
        return self

    def diff(self):
        ''' (MongoORM) -> dict
        Returns a dictionary containing changes between this MongoORM's
        current and original states.
        '''

        return self._current

    def commit(self):
        ''' (MongoORM) -> MongoORM
        Updates this MongoORM's document in its linked collection.
        '''

        if (self._original != self._current):
            self.source.update_one(
                {
                    '_id': self.getId()
                },
                {

                    # only set the differences between the original 
                    # and current set
                    '$set': self.diff()
                }
            )

            # all changes committed, so reset to current
            self.reset(True)
        return self

    def remove(self):
        ''' (MongoORM) -> MongoORM
        Removes this MongoORM from the database completely.
        '''

        self.source.remove({'_id': self.getId()})
        return self

    def getId(self):
        ''' (MongoORM) -> ObjectId
        Gets the ObjectId associated with this MongoORM.
        '''

        return self.getOriginal('_id')

    def set(self, field, value):
        ''' (MongoORM, object, object) -> MongoORM
        Sets the value of field to value.
        '''

        self._current[field] = value
        return self

    def updateList(self, field):
        ''' (MongoORM, object) -> list
        Returns the list at field for modification.
        '''

        # replicate in current
        if field not in self._current:
            self.set(field, self.getOriginal(field))
        return self.get(field)

    def push(self, field, value):
        ''' (MongoORM, object, object) -> MongoORM
        Appends value to the list field.

        REQ: field's value is a list
        '''

        self.updateList(field).append(value)
        return self

    def pop(self, field, index=0):
        ''' (MongoORM, object) -> object
        Removes and returns the first element in the list at field.
        '''

        return self.updateList(field).pop(index)
        
    def get(self, field):
        ''' (MongoORM, object) -> object
        Gets the current value of field.
        '''

        return self._current.get(field, self.getOriginal(field))

    def getOriginal(self, field):
        ''' (MongoORM, object) -> object
        Gets the original value of field before any uncommitted changes.
        '''

        return deepcopy(self._original.get(field))