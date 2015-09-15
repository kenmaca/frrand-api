def new(commentId):
    ''' (ObjectId) -> tuple
    Used to alert the Request owner that a new Comment was posted.
    '''

    return ('newRequestComment', commentId)