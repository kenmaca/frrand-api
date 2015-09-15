def newInvite(inviteId):
    ''' (ObjectId) -> tuple
    Used to alert an User that an Invite was generated for them.
    '''

    return ('requestInvite', inviteId)

def created(addressId):
    ''' (ObjectId) -> tuple
    Used to notify an User that a new permanent Address was generated for them.
    '''

    return ('addressCreated', addressId)