import os

from tiddlyweb.model.recipe import Recipe

from tiddlywebplugins.gitstore import run

from . import store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_recipe_put():
    recipe = Recipe('omega')
    STORE.put(recipe)

    store_root = os.path.join(TMPDIR, 'test_store')
    recipe_filename = os.path.join(store_root, 'recipes', 'omega')
    assert os.path.isfile(recipe_filename)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: recipe put: omega'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''


def test_recipe_delete():
    recipe = Recipe('omega')
    STORE.put(recipe)
    STORE.delete(recipe)

    store_root = os.path.join(TMPDIR, 'test_store')
    recipe_filename = os.path.join(store_root, 'recipes', 'omega')
    assert not os.path.isfile(recipe_filename)
    info = run('git', 'log', '-n1', '--format=%ae %ce: %s', cwd=store_root)
    assert info.strip() == \
            'JohnDoe@example.com tiddlyweb@example.com: recipe delete: omega'
    assert run('git', 'diff', '--exit-code', cwd=store_root) == ''
