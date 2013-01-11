import os
import shutil
import tempfile

import mangler

from tiddlyweb.store import Store


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
