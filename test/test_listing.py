import os
import re

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoBagError, NoTiddlerError

from tiddlywebplugins.gitstore import run

from pytest import raises

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_list_tiddlers():
    bag = Bag('alpha')
    STORE.put(bag)

    for title in ['Foo', 'Bar', 'Baz']:
        tiddler = Tiddler(title, bag.name)
        STORE.put(tiddler)

    bag = Bag(bag.name)
    tiddlers = STORE.list_bag_tiddlers(bag)
    titles = [tiddler.title for tiddler in tiddlers]

    assert 'Foo' in titles
    assert 'Bar' in titles
    assert 'Baz' in titles

    bag = Bag('bravo')
    tiddlers = STORE.list_bag_tiddlers(bag)
    with raises(NoBagError):
        list(tiddlers)


def test_list_tiddler_revisions():
    bag = Bag('alpha')
    STORE.put(bag)

    for text in ['lipsum', 'lorem ipsum', 'lorem ipsum\ndolor sit amet']:
        tiddler = Tiddler('FooBar', bag.name)
        tiddler.text = text
        STORE.put(tiddler)

    tiddler = Tiddler('FooBar', bag.name)
    revisions = STORE.list_tiddler_revisions(tiddler)
    assert len(revisions) == 3
    assert re.match('^[a-z0-9]{40}$', revisions[1])

    tiddler = Tiddler('N/A', bag.name)
    with raises(NoTiddlerError):
        STORE.list_tiddler_revisions(tiddler)
