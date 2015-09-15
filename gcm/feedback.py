def feedbackSubmitted(feedbackId):
    ''' (ObjectId) -> tuple
    Used to notify an User that a Feedback was submitted for them.
    '''

    return ('feedbackSubmitted', feedbackId)