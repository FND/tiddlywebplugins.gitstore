import os
import shutil
import tempfile

import wsgi_intercept

import mangler

from wsgi_intercept import httplib2_intercept

from tiddlyweb.store import Store
from tiddlyweb.config import config
from tiddlyweb.web.serve import load_app


def initialize_app(cfg):
    config.update(cfg) # XXX: side-effecty
    config['server_host'] = {
        'scheme': 'http',
        'host': 'example.org',
        'port': '8001',
    }

    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('example.org', 8001, lambda: load_app())

    return config


def store_setup():
    tmpdir = tempfile.mkdtemp()

    config = {
        'server_host': {
            'scheme':'http',
            'host':'example.com',
            'port': 80
        },
        'server_store': ['tiddlywebplugins.gitstore', {
            'store_root': os.path.join(tmpdir, 'test_store')
        }]
    }
    environ = {
        'tiddlyweb.config': config,
        'tiddlyweb.usersign': { 'name': 'JohnDoe' }
    }

    store = Store(config['server_store'][0], config['server_store'][1], environ)

    return store, tmpdir


def store_teardown(tmpdir):
    shutil.rmtree(tmpdir)
