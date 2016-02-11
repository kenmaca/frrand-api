def newRequestComment(commentId):
    ''' (ObjectId) -> tuple
    Used to alert the Request owner that a new Comment was posted.
    '''

    return ('newRequestComment', commentId)

def newPublicComment(commentId, publicInviteId):
    ''' (ObjectId, ObjectId) -> tuple
    Used to alert a subscriber of a PublicInvite that a new Comment was posted.
    '''

    return ('newPublicComment', '%s,%s' % (commentId, publicInviteId))

def newInviteComment(commentId, inviteId):
    ''' (ObjectId, ObjectId) -> tuple
    Used to alert a subscriber of an Invite that a new Comment was posted.
    '''

    return ('newInviteComment', '%s,%s' % (commentId, inviteId))
