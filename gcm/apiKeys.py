def loggedIn(apiKey, userId, deviceId):
    ''' (str, ObjectId) -> tuple
    Used to broadcast an User's apiKey to them.
    '''

    return (
        'apiKey',
        {
            'apiKey': apiKey,
            'userId': userId
        },
        deviceId
    )