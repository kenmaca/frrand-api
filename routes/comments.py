from flask import current_app as app, g
import messages.comments

schema = {
    'requestId': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'requests',
            'field': '_id'
        },
        'required': True
    },
    'createdBy': {
        'type': 'objectid',
        'data_relation': {
            'resource': 'users',
            'field': '_id'
        },
        'readonly': True
    },
    'comment': {
        'type': 'string',
        'minlength': 1,
        'maxlength': 240,
        'required': True
    }
}

config = {
    'item_title': 'comment',
    'public_methods': [],
    'public_item_methods': [],
    'allowed_filters': ['requestId'],
    'item_methods': ['GET'],
    'resource_methods': ['GET', 'POST'],
    'auth_field': None,
    'schema': schema
}

def init(app):
    ''' (LocalProxy) -> NoneType
    Adds this route's specific hooks to this route.
    '''

    app.on_inserted_comments += onInserted

# on_inserted_comments
def onInserted(insertedComments):
    ''' (dict) -> NoneType
    An Eve hook used after insertion.
    '''

    for insertedComment in insertedComments:
        import models.comments as comments
        
        # set owner
        comment = comments.Comment(
            app.data.driver.db,
            comments.Comment.collection,
            **insertedComment
        ).setOwner(g.get('auth_value')).commit()

        request = comment.getRequest()
        owner = request.getOwner()
        subscribed = []
        invitees = {}

        # update numberOfComments
        request.set(
            'numberOfComments',
            len(request.getComments())
        ).commit()

        # add the owner
        if owner not in subscribed:
            subscribed.append(owner)

        # now, add all invitees
        for invite in request.getInvites():
            invitee = invite.getOwner()
            if invitee not in subscribed:
                subscribed.append(invitee)

                # store invitees since we want to pass them to their own
                # invite and not the public one
                invitees[invitee.getId()] = invite

        # and finally, all commenters if the Request was public
        if request.isPublic():
            for c in request.getComments():
                commenter = c.getOwner()
                if commenter not in subscribed:
                    subscribed.append(commenter) 

        for subscriber in subscribed:

            # prevent gcm to comment author
            if subscriber.getId() != comment.getOwner().getId():

                # first, Request owner
                if subscriber.getId() == owner.getId():
                    subscriber.message(
                        *messages.comments.newRequestComment(comment.getId())
                    )

                # if it's an Invite, send them to their own Invite display
                elif subscriber.getId() in invitees:
                    subscriber.message(
                        *messages.comments.newInviteComment(
                            comment.getId(),
                            invitees[subscriber.getId()].getId()
                        )
                    )

                # otherwise it's Public
                else:
                    subscriber.message(
                        *messages.comments.newPublicComment(
                            comment.getId(),
                            request.getPublic().getId()
                        )
                    )
