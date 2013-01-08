import os
import shutil
import tempfile

from tiddlywebplugins.utils import get_store


def setup_module(module):
    module.TMPDIR = tempfile.mkdtemp()
    module.CONFIG = {
        'server_store': ['tiddlywebplugins.gitstore', {
            'store_root': os.path.join(TMPDIR, 'test_store')
        }],
    }
    module.STORE = get_store(CONFIG)
    module.ENVIRON = { 'tiddlyweb.config': CONFIG }


def teardown_module(module):
    shutil.rmtree(TMPDIR)


def test_initialize_store():
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
