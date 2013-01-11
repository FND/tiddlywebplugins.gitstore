import os
import subprocess

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_tiddler_put():
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
