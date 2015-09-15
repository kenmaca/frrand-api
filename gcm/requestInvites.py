def accepted(inviteId):
    ''' (ObjectId) -> tuple
    Used to notify the owner of the Request that an Invite was accepted.
    '''

    return ('requestInviteAccepted', inviteId)

def attached(inviteId):
    ''' (ObjectId) -> tuple
    Used to notify the owner of the Invite (the deliverer) that their
    invite was attached by the owner of the Request.
    '''

    return ('requestInviteAttached', inviteId)

def completed(inviteId):
    ''' (ObjectId) -> tuple
    Used to notify the owner of the Invite (the deliverer) that their
    invite was completed by the owner of the Request.
    '''

    return ('requestInviteCompleted', inviteId)