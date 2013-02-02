import os

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler

from tiddlywebplugins.gitstore import run

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()

    module.STORE_ROOT = os.path.join(TMPDIR, 'test_store')

    module.BAG = Bag('alpha')
    STORE.put(BAG)


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_file_separation():
    STORE_ROOT = os.path.join(TMPDIR, 'test_store')

    tiddler = Tiddler('Foo', BAG.name)
    tiddler.type = 'application/binary'
    tiddler.text = 'lorem ipsum'
    STORE.put(tiddler)
    assert tiddler.text == 'lorem ipsum'
    assert tiddler.type == 'application/binary'

    bag_dir = os.path.join(STORE_ROOT, 'bags', 'alpha')
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
        assert len(lines[-1]) == 60 # body
    with open(bin_file) as fh:
        contents = fh.read()
        assert contents == 'lorem ipsum'

    stored_tiddler = STORE.get(Tiddler(tiddler.title, tiddler.bag))
    assert stored_tiddler.text == 'lorem ipsum'


def binary_data():
    pass # TODO (use SHA1 comparison)


def test_commit():
    tiddler = Tiddler('Bar', BAG.name)
    tiddler.type = 'application/binary'
    tiddler.text = 'lorem ipsum'
    STORE.put(tiddler)

    bag_dir = os.path.join(STORE_ROOT, 'bags', 'alpha')
    tiddler_file = os.path.join(bag_dir, 'tiddlers', 'Bar')
    binary_file = os.path.join(bag_dir, 'tiddlers', 'binaries', 'Bar')

    trevs = run('git', 'log', '--format=%h', '--', tiddler_file, cwd=STORE_ROOT)
    brevs = run('git', 'log', '--format=%h', '--', binary_file, cwd=STORE_ROOT)
    assert len(trevs.splitlines()) == 1
    assert len(brevs.splitlines()) == 1
    assert trevs == brevs

    tiddler.text = 'lorem ipsum\ndolor sit amet'
    STORE.put(tiddler)

    trevs = run('git', 'log', '--format=%h', '--', tiddler_file, cwd=STORE_ROOT)
    brevs = run('git', 'log', '--format=%h', '--', binary_file, cwd=STORE_ROOT)
    assert len(trevs.splitlines()) == 2
    assert len(brevs.splitlines()) == 2
    assert trevs == brevs


def test_deletion():
    pass # TODO: ensure deletion also removes binary


def test_listing():
    pass # TODO: ensure tiddler listings ignore "binaries" directory
