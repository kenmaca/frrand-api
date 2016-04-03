#!/usr/bin/python3

from eve import Eve
from eve_docs import eve_docs
from flask_bootstrap import Bootstrap
from flask import render_template, send_from_directory, request, Response
from functools import wraps
import os
from utils.auth import APIAuth
from settings import init
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options

admin_directory = os.path.dirname(os.path.abspath(__file__)) + '/admin-panel'

# start eve
app = Eve(auth=APIAuth(), static_folder=admin_directory)
init(app)

# basic protection for admin-panel
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'fr@@@nd'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# admin-panel SPA
@app.route('/panel')
@requires_auth
def admin_panel():
  return send_from_directory(admin_directory, 'index.html')

# eve_docs addon
Bootstrap(app)
app.register_blueprint(eve_docs, url_prefix='/docs')

if __name__ == '__main__':

    # run
    tornado.options.parse_command_line()
    server = HTTPServer(WSGIContainer(app), ssl_options={
        'certfile': 'dev-api.frrand.com.crt',
        'keyfile': 'dev-api.frrand.com.key'
    })
    server.listen(443)
    IOLoop.instance().start()
