import os

from tiddlyweb.model.bag import Bag

from tiddlywebplugins.gitstore import run

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_bag_put():
    bag = Bag('alpha')
    STORE.put(bag)

    store_root = os.path.join(TMPDIR, 'test_store')
    bag_dir = os.path.join(store_root, 'bags', 'alpha')
    assert os.path.isdir(bag_dir)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: bag put: alpha'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''


def test_bag_delete():
    bag = Bag('alpha')
    STORE.put(bag)
    STORE.delete(bag)

    store_root = os.path.join(TMPDIR, 'test_store')
    bag_dir = os.path.join(store_root, 'bags', 'alpha')
    assert not os.path.isdir(bag_dir)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: bag delete: alpha'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''
