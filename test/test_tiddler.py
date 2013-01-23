import os
import re
import subprocess

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoTiddlerError

from tiddlywebplugins.gitstore import run

from pytest import raises

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_tiddler_get():
    bag = Bag('alpha')
    STORE.put(bag)

    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum\ndolor sit amet'
    tiddler.tags = ['foo', 'bar']
    STORE.put(tiddler)

    stored_tiddler = Tiddler('Foo', bag.name)
    stored_tiddler = STORE.get(stored_tiddler)
    assert stored_tiddler.revision == tiddler.revision

    missing_tiddler = Tiddler('Bar', bag.name)
    with raises(NoTiddlerError):
        STORE.get(missing_tiddler)


def test_revision_get():
    bag = Bag('alpha')
    STORE.put(bag)

    # create a bunch of revisions
    tiddler_data = [
        { 'text': 'hello world', 'tags': ['foo'] },
        { 'text': 'lorem ipsum', 'tags': ['foo', 'bar'] },
        { 'text': 'lorem ipsum\ndolor sit amet', 'tags': [] }
    ]
    for tid in tiddler_data:
        tiddler = Tiddler('Foo', bag.name)
        tiddler.text = tid['text']
        tiddler.tags = tid['tags']
        STORE.put(tiddler)
        tid['revision'] = tiddler.revision

    tiddler = Tiddler('Foo', bag.name)
    tiddler.revision = None
    tiddler = STORE.get(tiddler)
    assert tiddler.text == 'lorem ipsum\ndolor sit amet'
    assert len(tiddler.tags) == 0

    for i, tid in enumerate(tiddler_data):
        tiddler = Tiddler('Foo', bag.name)
        tiddler.revision = tid['revision']
        tiddler = STORE.get(tiddler)
        assert tiddler.text == tid['text']
        assert len(tiddler.tags) == len(tid['tags'])

    tiddler = Tiddler('Foo', bag.name)
    tiddler.revision = 'N/A'
    with raises(NoTiddlerError):
        STORE.get(tiddler)


def test_tiddler_put():
    store_root = os.path.join(TMPDIR, 'test_store')

    bag = Bag('alpha')
    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum'
    tiddler.tags = ['foo', 'bar']

    STORE.put(bag)

    bag_dir = os.path.join(store_root, 'bags', 'alpha')
    assert os.path.isdir(bag_dir)
    assert os.path.isdir(os.path.join(bag_dir, 'tiddlers'))

    STORE.put(tiddler)

    tiddler_file = os.path.join(bag_dir, 'tiddlers', 'Foo')
    assert os.path.isfile(tiddler_file)
    assert re.match('^[a-z0-9]{40}$', tiddler.revision)
    with open(tiddler_file) as fh:
        contents = fh.read()
        assert 'tags: foo bar' in contents
        assert 'lorem ipsum' in contents
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: tiddler put'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''

    # ensure there are no undesirable side-effects

    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum\ndolor sit amet'
    tiddler.tags = ['foo']
    STORE.put(tiddler)

    assert tiddler.text == 'lorem ipsum\ndolor sit amet'
    assert tiddler.tags == ['foo']


def test_tiddler_delete():
    store_root = os.path.join(TMPDIR, 'test_store')

    bag = Bag('alpha')
    STORE.put(bag)

    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lipsum'
    STORE.put(tiddler)

    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum'
    STORE.put(tiddler)

    tiddler = Tiddler('Foo', bag.name)
    STORE.delete(tiddler)

    bag_dir = os.path.join(store_root, 'bags', 'alpha')
    tiddler_file = os.path.join(bag_dir, 'tiddlers', 'Foo')
    assert not os.path.isfile(tiddler_file)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: tiddler delete'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''

    missing_tiddler = Tiddler('Bar', bag.name)
    with raises(NoTiddlerError):
        STORE.delete(missing_tiddler)


def test_tiddler_creation_info():
    bag = Bag('alpha')
    STORE.put(bag)

    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum'
    tiddler.modifier = 'john'
    tiddler.modified = '20130119150632'
    STORE.put(tiddler)

    tiddler = Tiddler('Foo', bag.name)
    tiddler.text = 'lorem ipsum\ndolor sit amet'
    tiddler.modifier = 'jane'
    tiddler.modified = '20130119151021'
    STORE.put(tiddler)

    tiddler = Tiddler('Foo', bag.name)
    tiddler = STORE.get(tiddler)
    assert tiddler.creator == 'john'
    assert tiddler.modifier == 'jane'
    assert tiddler.created != tiddler.modified
    assert len(tiddler.created) == 14
    assert len(tiddler.fields) == 0
