#!/usr/bin/python3

from eve import Eve
from eve_docs import eve_docs
from flask_bootstrap import Bootstrap
from flask import render_template, send_from_directory
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

# admin-panel SPA
@app.route('/admin')
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
