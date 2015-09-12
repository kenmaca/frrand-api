#!/usr/local/bin/python3.4
from run import app

with app.test_request_context():

    # prune expired invites
    import models.requestInvites as invites
    import routes.requestInvites as invitesRoute
    for invite in app.data.driver.db['requestInvites'].find({}):
        invite = invites.Invite(
            app.data.driver.db,
            invites.Invite.collection,
            **invite
        )

        if invite.isExpired():
            invitesRoute._removeInvite(invite)
