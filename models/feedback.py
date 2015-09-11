import models.orm as orm

class Feedback(orm.MongoORM):
    ''' A representation of Feedback in Frrand.
    '''

    collection = 'feedback'

    @staticmethod
    def fromObjectId(db, objectId):
        ''' (pymongo.database.Database, bson.ObjectId) -> Feedback
        Creates Feedback directly from database with an ObjectId of objectId.
        '''

        return orm.MongoORM.fromObjectId(db, objectId, Feedback)

    @staticmethod
    def findOne(db, **query):
        ''' (pymongo.database.Database) -> Feedback
        Finds a single Feedback given query.
        '''

        return orm.MongoORM.findOne(db, Feedback, **query)

    @staticmethod
    def new(db, request, toInvitee=True):
        ''' (pymongo.database.Database,
            models.requests.Request, bool) -> Feedback
        Creates a new Feedback and writes to the database. The invite is
        created for the Invitee if toInvitee is True, otherwise, is for the
        requester.

        If toInvitee:
        REQ: request.get('rating') is not None

        Else:
        REQ: request.getAttached().get('rating') is not None
        '''

        invite = request.getAttached()
        target = invite.getOwner() if toInvitee else request.getOwner()
        feedback = db[Feedback.collection].insert(
            {
                'requestId': request.getId(),
                'requestInviteId': invite.getId(),
                'rating': request.get('rating')
                    if toInvitee
                    else invite.get('rating'),
                'comment': (
                    (request.get('comment')
                        if request.exists('comment') else ''
                    ) if toInvitee
                    else (invite.get('comment')
                        if invite.exists('comment') else ''
                    )
                ),
                'for': target.getId()
            }
        )

        # and add to user's feedback running average
        target.addRating(
            request.get('rating') if toInvitee else invite.get('rating')
        ).commit()

        # now alert the feedback recipient
        target.message('feedbackSubmitted', feedback)
