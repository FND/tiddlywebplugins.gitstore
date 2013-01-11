import os
import shutil
import tempfile

import mangler

from tiddlyweb.store import Store


def store_setup(module):
    module.TMPDIR = tempfile.mkdtemp()
    module.CONFIG = {
        'server_host': {
            'scheme':'http',
            'host':'example.com',
            'port': 80
        },
        'server_store': ['tiddlywebplugins.gitstore', {
            'store_root': os.path.join(module.TMPDIR, 'test_store')
        }]
    }
    module.ENVIRON = {
        'tiddlyweb.config': module.CONFIG,
        'tiddlyweb.usersign': { 'name': 'JohnDoe' }
    }
    module.STORE = Store(module.CONFIG['server_store'][0],
            module.CONFIG['server_store'][1], module.ENVIRON)


def store_teardown(module):
    shutil.rmtree(module.TMPDIR)
