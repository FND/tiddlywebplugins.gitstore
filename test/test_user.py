import os

from tiddlyweb.model.user import User

from tiddlywebplugins.gitstore import run

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_user_put():
    user = User('John', note='lorem ipsum')
    STORE.put(user)

    store_root = os.path.join(TMPDIR, 'test_store')
    user_filename = os.path.join(store_root, 'users', 'John')
    assert os.path.isfile(user_filename)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: user put: John'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''


def test_user_delete():
    user = User('John', note='lorem ipsum')
    STORE.put(user)
    STORE.delete(user)

    store_root = os.path.join(TMPDIR, 'test_store')
    user_filename = os.path.join(store_root, 'users', 'John')
    assert not os.path.isfile(user_filename)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: user delete: John'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''
