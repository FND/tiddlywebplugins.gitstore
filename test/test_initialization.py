import os

from . import store_setup, store_teardown


def setup_module(module):
    _, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_store_initialization():
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
