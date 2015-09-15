from gcm.locations import created

def newInvite(inviteId):
    ''' (ObjectId) -> tuple
    Used to alert an User that an Invite was generated for them.
    '''

    return ('requestInvite', inviteId)