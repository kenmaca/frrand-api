#!/usr/bin/python3

from eve import Eve
from eve_docs import eve_docs
from flask_bootstrap import Bootstrap
from utils.auth import APIAuth
from settings import init
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options

# start eve
app = Eve(auth=APIAuth())
init(app)

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
