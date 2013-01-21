import os

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import NoBagError

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
    tiddlers = STORE.list_bag_tiddlers(bag) # XXX: this should raise already!?
    with raises(NoBagError):
        list(tiddlers)
