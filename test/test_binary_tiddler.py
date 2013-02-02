import os

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_file_separation():
    store_root = os.path.join(TMPDIR, 'test_store')

    bag = Bag('alpha')
    STORE.put(bag)

    tiddler = Tiddler('Foo', bag.name)
    tiddler.type = 'application/binary'
    tiddler.text = 'lorem ipsum'
    STORE.put(tiddler)
    assert tiddler.text == 'lorem ipsum'
    assert tiddler.type == 'application/binary'

    bag_dir = os.path.join(store_root, 'bags', 'alpha')
    tiddlers_dir = os.path.join(bag_dir, 'tiddlers')
    tiddler_file = os.path.join(tiddlers_dir, 'Foo')
    bin_dir = os.path.join(tiddlers_dir, 'binaries')
    bin_file = os.path.join(bin_dir, 'Foo')
    assert os.path.isfile(tiddler_file)
    assert os.path.isdir(bin_dir)
    assert os.path.isfile(bin_file)
    with open(tiddler_file) as fh:
        contents = fh.read()
        assert 'type: application/binary' in contents
        assert 'lorem ipsum' not in contents
        lines = contents.splitlines()
        assert ': ' in lines[-3] # header
        assert lines[-2] == '' # separator
        assert lines[-1] == '' # body
    with open(bin_file) as fh:
        contents = fh.read()
        assert contents == 'lorem ipsum'

    stored_tiddler = STORE.get(Tiddler(tiddler.title, tiddler.bag))
    assert stored_tiddler.text == 'lorem ipsum'


def test_commit():
    pass # TODO ensure binary is committed


def test_deletion():
    pass # TODO: ensure deletion also removes binary


def test_listing():
    pass # TODO: ensure tiddler listings ignore "binaries" directory
