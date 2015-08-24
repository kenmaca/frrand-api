#!/usr/local/bin/python3.4

from eve import Eve
from eve_docs import eve_docs
from flask_bootstrap import Bootstrap
from utils.auth import APIAuth
from settings import init

# start eve
app = Eve(auth=APIAuth())
init(app)

# eve_docs addon
Bootstrap(app)
app.register_blueprint(eve_docs, url_prefix='/docs')

if __name__ == '__main__':

    # run
    app.run(host='0.0.0.0')
