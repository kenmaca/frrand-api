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

        # now message request owner
        subscribed = []
        [
            subscribed.append(c.getOwner())
            for c in comment.getRequest().getComments()
            if c not in subscribed
        ]

        for subscriber in subscribed:

            # prevent gcm to comment author
            if subscriber.getId() != comment.getOwner().getId():

                # first, Request owner
                if subscriber.getId() == comment.getRequest().getOwner().getId():
                    subscriber.message(
                        *messages.comments.newRequestComment(comment.getId())
                    )

                # otherwise it's Public
                elif comment.getRequest().isPublic():
                    subscriber.message(
                        *messages.comments.newPublicComment(
                            comment.getId(),
                            comment.getRequest().getPublic().getId()
                        )
                    )

                # and finally the most restrictive, an Invite
                else:
                    try:
                        subscriber.message(
                            *messages.comments.newInviteComment(
                                comment.getId(),
                                [
                                    invite for invite
                                    in comment.getRequest().getInvites()
                                    if subscriber.getId() == invite.getOwner().getId()
                                ][0].getId()
                            )
                        )
                    except IndexError:
                        pass
