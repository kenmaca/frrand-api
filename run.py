#!/usr/local/bin/python3.4

from eve import Eve
from eve_docs import eve_docs
from flask_bootstrap import Bootstrap
from utils.auth import APIAuth
from utils.hooks import *

if __name__ == '__main__':
    app = Eve(auth=APIAuth)

    # custom hooks
    app.on_insert_locations += supplementLocationData
    app.on_inserted_requestInvites += requestInviteSendGcm
    app.on_inserted_requests += generateRequestInvites
    app.on_inserted_users += initNewUser
    app.on_insert_apiKeys += provisionApiKey

    # eve_docs addon
    Bootstrap(app)
    app.register_blueprint(eve_docs, url_prefix='/docs')

    # run
    app.run(host='0.0.0.0')
