def created(addressId):
    ''' (ObjectId) -> tuple
    Used to notify an User that a new permanent Address was generated for them.
    '''

    return ('addressCreated', addressId)