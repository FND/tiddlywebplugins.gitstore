import os
import hashlib

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.serializer import TiddlerFormatError
from tiddlyweb.util import sha

from tiddlywebplugins.gitstore import run

from pytest import raises

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
    bin_dir = os.path.join(tiddlers_dir, '_binaries')
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


def test_binary_data():
    cwd = os.path.dirname(__file__)
    image_filename = os.path.join(cwd, 'floppy.jpg')

    tiddler = Tiddler('Floppy', BAG.name)
    tiddler.type = 'image/jpeg'
    with open(image_filename, 'rb') as fh:
        tiddler.text = fh.read()
    STORE.put(tiddler)

    bag_dir = os.path.join(STORE_ROOT, 'bags', 'alpha')
    tiddlers_dir = os.path.join(bag_dir, 'tiddlers')
    tiddler_file = os.path.join(tiddlers_dir, 'Floppy')
    bin_dir = os.path.join(tiddlers_dir, '_binaries')
    bin_file = os.path.join(bin_dir, 'Floppy')

    source_sha1 = file_checksum(image_filename)
    bin_sha1 = file_checksum(bin_file)
    assert bin_sha1 == source_sha1
    stored_tiddler = STORE.get(Tiddler(tiddler.title, tiddler.bag))
    assert sha(stored_tiddler.text).hexdigest() == source_sha1


def test_commit():
    tiddler = Tiddler('Bar', BAG.name)
    tiddler.type = 'application/binary'
    tiddler.text = 'lorem ipsum'
    STORE.put(tiddler)

    bag_dir = os.path.join(STORE_ROOT, 'bags', 'alpha')
    tiddler_file = os.path.join(bag_dir, 'tiddlers', 'Bar')
    binary_file = os.path.join(bag_dir, 'tiddlers', '_binaries', 'Bar')

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

    STORE.delete(tiddler)

    trevs = run('git', 'log', '--format=%h', '--', tiddler_file, cwd=STORE_ROOT)
    brevs = run('git', 'log', '--format=%h', '--', binary_file, cwd=STORE_ROOT)
    assert len(trevs.splitlines()) == 3
    assert len(brevs.splitlines()) == 3
    assert trevs == brevs


def test_deletion():
    tiddler = Tiddler('Baz', BAG.name)
    tiddler.type = 'application/binary'
    tiddler.text = 'lorem ipsum'
    STORE.put(tiddler)

    bag_dir = os.path.join(STORE_ROOT, 'bags', 'alpha')
    tiddler_file = os.path.join(bag_dir, 'tiddlers', 'Baz')
    binary_file = os.path.join(bag_dir, 'tiddlers', '_binaries', 'Baz')

    assert os.path.isfile(tiddler_file)
    assert os.path.isfile(binary_file)

    STORE.delete(tiddler)

    assert not os.path.isfile(tiddler_file)
    assert not os.path.isfile(binary_file)


def test_tiddler_listing():
    bag = Bag('bravo')
    STORE.put(bag)

    tiddlers = STORE.list_bag_tiddlers(bag)
    assert len(list(tiddlers)) == 0

    tiddler = Tiddler('Foo', bag.name)
    tiddler.type = 'application/binary'
    STORE.put(tiddler)

    tiddlers = STORE.list_bag_tiddlers(bag)
    titles = [tiddler.title for tiddler in tiddlers]
    assert len(titles) == 1

    tiddler = Tiddler('Bar', bag.name)
    STORE.put(tiddler)

    tiddlers = STORE.list_bag_tiddlers(bag)
    titles = [tiddler.title for tiddler in tiddlers]
    assert len(titles) == 2

    tiddler = Tiddler('Baz', bag.name)
    tiddler.type = 'image/png'
    STORE.put(tiddler)

    tiddlers = STORE.list_bag_tiddlers(bag)
    titles = [tiddler.title for tiddler in tiddlers]
    assert len(titles) == 3


def test_revision_listing():
    contents = ['lipsum', 'lorem ipsum', 'lorem ipsum\ndolor sit amet']
    for i, text in enumerate(contents):
        tiddler = Tiddler('FooBar', BAG.name)
        tiddler.text = text
        tiddler.type = None if i % 2 == 0 else 'application/binary'
        STORE.put(tiddler)

    tiddler = Tiddler('FooBar', BAG.name)
    revisions = STORE.list_tiddler_revisions(tiddler)
    assert len(revisions) == 3


def test_title_conflicts():
    bag = Bag('charlie')
    STORE.put(bag)

    for bag_name in ['alpha', 'charlie']:
        tiddler = Tiddler('binaries', BAG.name)
        tiddler.text = '...'
        STORE.put(tiddler) # should not raise

        stored_tiddler = Tiddler(tiddler.title, BAG.name)
        stored_tiddler = STORE.get(stored_tiddler)
        assert stored_tiddler.text == '...'

        tiddler = Tiddler('_binaries', BAG.name)
        tiddler.text = '...'
        with raises(TiddlerFormatError):
            assert STORE.put(tiddler)


def file_checksum(filename):
    return sha(open(filename).read()).hexdigest()
