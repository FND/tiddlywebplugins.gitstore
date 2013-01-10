import os
import shutil
import subprocess
import tempfile

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import Store


def setup_module(module):
    module.TMPDIR = tempfile.mkdtemp()
    module.CONFIG = {
        'server_host': {
            'scheme':'http',
            'host':'example.com',
            'port': 80
        },
        'server_store': ['tiddlywebplugins.gitstore', {
            'store_root': os.path.join(TMPDIR, 'test_store')
        }]
    }
    module.ENVIRON = {
        'tiddlyweb.config': CONFIG,
        'tiddlyweb.usersign': { 'name': 'JohnDoe' }
    }
    module.STORE = Store(CONFIG['server_store'][0], CONFIG['server_store'][1],
            ENVIRON)


def teardown_module(module):
    shutil.rmtree(TMPDIR)


def test_initialize_store():
    store_root = os.path.join(TMPDIR, 'test_store')
    assert os.path.isdir(store_root)
    directories = [dirpath.replace(TMPDIR, '.') for
            (dirpath, dirnames, filenames) in os.walk(store_root)
            if not os.path.sep.join(['', '.git', '']) in dirpath]
    assert len(directories) == 5
    assert './test_store' in directories
    assert './test_store/bags' in directories
    assert './test_store/recipes' in directories
    assert './test_store/users' in directories
    assert './test_store/.git' in directories


def test_tiddler_put(): # TODO: does not belong into this module
    store_root = os.path.join(TMPDIR, 'test_store')

    bag = Bag('alpha')
    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum\ndolor sit amet'
    tiddler.tags = ['foo', 'bar']

    STORE.put(bag)

    bag_dir = os.path.join(store_root, 'bags', 'alpha')
    assert os.path.isdir(bag_dir)
    assert os.path.isdir(os.path.join(bag_dir, 'tiddlers'))

    STORE.put(tiddler)

    tiddler_file = os.path.join(bag_dir, 'tiddlers', 'Foo')
    assert os.path.isfile(tiddler_file)
    assert len(tiddler.revision) == 40
    with open(tiddler_file) as fh:
        contents = fh.read()
        assert 'tags: foo bar' in contents
        assert tiddler.text in contents
    info = subprocess.check_output(['git', 'log', '-n1',
            '--format=%h %ae %ce: %s'], cwd=store_root)
    assert info.strip()[8:] == \
            'JohnDoe@example.com tiddlyweb@example.com: tiddler put'
