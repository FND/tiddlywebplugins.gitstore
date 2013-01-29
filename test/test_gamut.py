"""
adapted from tiddlywebplugins.sqlalchemy:
https://github.com/cdent/tiddlywebplugins.sqlalchemy/blob/master/test/test_gamut.py
"""

import os

import py.test

from base64 import b64encode

from tiddlyweb.config import config
from tiddlyweb.store import Store, NoBagError, NoUserError, NoRecipeError, NoTiddlerError

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import Policy
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.user import User

from . import store_setup, store_teardown


RANGE = 10


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_make_a_bunch():
    for x in xrange(RANGE):
        bag_name = u'bag%s' % x
        recipe_name = u'recipe%s' % x
        tiddler_name = u'tiddler%s' % x
        recipe_list = [(bag_name, '')]
        tiddler_text = u'hey ho %s' % x
        field_name = u'field%s' % x
        tag_name = u'tag%s' % x
        user_name = u'user%s' % x
        user_pass = u'pass%s' % x
        user_note = u'note%s' % x
        user_roles = [u'rolehold', u'role%s' % x]

        bag = Bag(bag_name)
        bag.policy.owner = u'owner%s' % x
        bag.policy.read = [u'hi%s' % x, u'andextra']
        bag.policy.manage = [u'R:hi%s' % x, u'andmanage']
        STORE.put(bag)
        recipe = Recipe(recipe_name)
        recipe.policy.owner = u'owner%s' % x
        recipe.policy.read = [u'hi%s' % x, u'andextra']
        recipe.policy.manage = [u'R:hi%s' % x, u'andmanage']
        recipe.set_recipe(recipe_list)
        STORE.put(recipe)
        tiddler = Tiddler(tiddler_name, bag_name)
        tiddler.text = tiddler_text
        tiddler.fields[field_name] = field_name
        tiddler.fields['server.host'] = u'gunky'
        tiddler.tags = [tag_name]
        STORE.put(tiddler)
        user = User(user_name)
        user.set_password(user_pass)
        user.note = user_note
        for role in user_roles:
            user.add_role(role)
        STORE.put(user)

    bags = [bag.name for bag in STORE.list_bags()]
    recipes = [recipe.name for recipe in STORE.list_recipes()]
    users = [user.usersign for user in STORE.list_users()]
    assert len(bags) == RANGE
    assert len(recipes) == RANGE
    assert len(users) == RANGE
    for x in xrange(RANGE):
        bname = u'bag%s' % x
        rname = u'recipe%s' % x
        uname = u'user%s' % x
        assert bname in bags
        assert rname in recipes
        assert uname in users

    bag = Bag('bag0')
    bag = STORE.get(bag)
    tiddlers = []
    for tiddler in STORE.list_bag_tiddlers(bag):
        tiddlers.append(STORE.get(tiddler))
    assert len(tiddlers) == 1
    assert tiddlers[0].title == 'tiddler0'
    assert tiddlers[0].fields['field0'] == 'field0'
    assert tiddlers[0].tags == ['tag0']
    assert sorted(bag.policy.read) == ['andextra', 'hi0']
    assert sorted(bag.policy.manage) == ['R:hi0', 'andmanage']
    assert bag.policy.owner == 'owner0'

    bag = Bag('bag0')
    bag = STORE.get(bag)
    bag.policy.read.remove('hi0')
    STORE.put(bag)
    bag = Bag('bag0')
    bag = STORE.get(bag)
    assert bag.policy.read == [u'andextra']

    bag = Bag('bag0')
    bag = STORE.get(bag)
    bag.policy.read.append(u'hi0')
    STORE.put(bag)
    bag = Bag('bag0')
    bag = STORE.get(bag)
    assert sorted(bag.policy.read) == ['andextra', 'hi0']

    user = User('user1')
    user = STORE.get(user)
    assert user.usersign == 'user1'
    assert user.check_password('pass1')
    assert user.note == 'note1'
    assert 'role1' in user.list_roles()
    assert 'rolehold' in user.list_roles()

    recipe = Recipe('recipe2')
    recipe = STORE.get(recipe)
    assert recipe.name == 'recipe2'
    bags = [bag_name for bag_name, filter in recipe.get_recipe()]
    assert len(bags) == 1
    assert 'bag2' in bags
    assert sorted(recipe.policy.read) == ['andextra', 'hi2']
    assert sorted(recipe.policy.manage) == ['R:hi2', 'andmanage']
    assert recipe.policy.owner == 'owner2'

    recipe.policy.manage = [u'andmanage']
    STORE.put(recipe)

    recipe = Recipe('recipe2')
    recipe = STORE.get(recipe)
    assert recipe.policy.manage == ['andmanage']

    # delete the above things
    STORE.delete(bag)
    py.test.raises(NoBagError, 'STORE.delete(bag)')
    py.test.raises(NoBagError, 'STORE.get(bag)')
    STORE.delete(recipe)
    py.test.raises(NoRecipeError, 'STORE.delete(recipe)')
    py.test.raises(NoRecipeError, 'STORE.get(recipe)')
    STORE.delete(user)
    py.test.raises(NoUserError, 'STORE.delete(user)')
    py.test.raises(NoUserError, 'STORE.get(user)')

    tiddler = Tiddler('tiddler9', 'bag9')
    STORE.get(tiddler)
    assert tiddler.bag == 'bag9'
    assert tiddler.text == 'hey ho 9'
    assert tiddler.tags == ['tag9']
    assert tiddler.fields['field9'] == 'field9'
    assert 'server.host' not in tiddler.fields
    STORE.delete(tiddler)
    tiddler = Tiddler('tiddler9', 'bag9')
    py.test.raises(NoTiddlerError, 'STORE.delete(tiddler)')
    py.test.raises(NoTiddlerError, 'STORE.get(tiddler)')


def test_handle_empty_policy():
    bag = Bag('empty')
    STORE.put(bag)
    new_bag = STORE.get(Bag('empty'))
    assert new_bag.policy.read == []
    assert new_bag.policy.manage == []
    assert new_bag.policy.create == []
    assert new_bag.policy.write == []
    assert new_bag.policy.accept == []
    assert new_bag.policy.owner is None


def test_reuse_policy_object():
    """
    Explicitly test a bug fix in policy handling wherein the owner
    field could get transformed into (and stay) a list thus ruining
    second use. Not that second use is encourage, but it could happen.
    """
    policy = Policy()
    policy.owner = u'campy'
    bag = Bag('policytest1')
    bag.policy = policy
    STORE.put(bag)
    bag = Bag('policytest2')
    bag.policy = policy
    STORE.put(bag)

    bag1 = STORE.get(Bag('policytest1'))
    bag2 = STORE.get(Bag('policytest2'))
    assert bag1.policy.owner == 'campy'
    assert bag2.policy.owner == 'campy'
    assert bag1.policy.owner == bag2.policy.owner


def test_tiddler_revisions():
    bag_name = u'bag8'
    for i in xrange(20):
        tiddler = Tiddler(u'oh hi', bag_name)
        tiddler.text = u'%s times we go' % i
        tiddler.fields[u'%s' % i] = u'%s' % i
        STORE.put(tiddler)

    revisions = STORE.list_tiddler_revisions(Tiddler('oh hi', bag_name))
    assert len(revisions) == 20
    tiddler = Tiddler('oh hi', bag_name)

    tiddler.revision = 90
    py.test.raises(NoTiddlerError, 'STORE.get(tiddler)')

    py.test.raises(NoBagError,
            'STORE.list_tiddler_revisions(Tiddler("sleepy", "cow"))')


def test_interleaved_tiddler_revisions():
    bag_name = u'bag8'
    for i in xrange(20):
        tiddler1 = Tiddler(u'oh yes', bag_name)
        tiddler2 = Tiddler(u'oh no', bag_name)
        tiddler1.text = u'%s times we yes' % i
        tiddler2.text = u'%s times we no' % i
        tiddler1.fields[u'%s' % i] = u'%s' % i
        tiddler2.fields[u'%s' % i] = u'%s' % i
        STORE.put(tiddler1)
        STORE.put(tiddler2)

    revisions = STORE.list_tiddler_revisions(Tiddler('oh yes', bag_name))
    assert len(revisions) == 20

    tiddler = Tiddler('oh yes', bag_name)
    tiddler.revision = 90
    py.test.raises(NoTiddlerError, 'STORE.get(tiddler)')

    py.test.raises(NoBagError,
            'STORE.list_tiddler_revisions(Tiddler("sleepy", "cow"))')


def test_tiddler_no_bag():
    tiddler = Tiddler('hi')
    py.test.raises(NoBagError, 'STORE.put(tiddler)')


def test_list_tiddlers_no_bag():
    bag = Bag('carne')
    try:
        py.test.raises(NoBagError, 'STORE.list_bag_tiddlers(bag).next()')
    except AttributeError:
        assert True


def test_2bag_policy():
    bag = Bag('pone')
    bag.policy.read = [u'cdent']
    bag.policy.write = [u'cdent']
    STORE.put(bag)

    bag = Bag('ptwo')
    bag.policy.read = [u'cdent', u'fnd']
    bag.policy.write = [u'cdent']
    STORE.put(bag)

    pone = STORE.get(Bag('pone'))
    ptwo = STORE.get(Bag('ptwo'))

    assert pone.policy.read == ['cdent']
    assert pone.policy.write == ['cdent']

    assert sorted(ptwo.policy.read) == ['cdent', 'fnd']
    assert ptwo.policy.write == ['cdent']

    STORE.delete(pone)

    ptwo = STORE.get(Bag('ptwo'))

    assert sorted(ptwo.policy.read) == ['cdent', 'fnd']
    assert ptwo.policy.write == ['cdent']

    bag = Bag('pone')
    bag.policy.read = [u'cdent']
    bag.policy.write = [u'cdent']
    STORE.put(bag)

    pone = STORE.get(Bag('pone'))
    assert pone.policy.read == ['cdent']
    assert pone.policy.write == ['cdent']

    pone.policy.read.append(u'fnd')

    STORE.put(pone)

    pone = STORE.get(Bag('pone'))

    assert sorted(pone.policy.read) == ['cdent', 'fnd']

    pone.policy.read = [u'cdent']
    STORE.put(pone)

    pone2 = STORE.get(Bag('pone'))
    assert pone2.policy.read == ['cdent']


def test_2recipe_policy():
    recipe = Recipe('pone')
    recipe.policy.read = [u'cdent']
    recipe.policy.write = [u'cdent']
    STORE.put(recipe)

    recipe = Recipe('ptwo')
    recipe.policy.read = [u'cdent', u'fnd']
    recipe.policy.write = [u'cdent']
    STORE.put(recipe)

    pone = STORE.get(Recipe('pone'))
    ptwo = STORE.get(Recipe('ptwo'))

    assert pone.policy.read == ['cdent']
    assert pone.policy.write == ['cdent']

    assert sorted(ptwo.policy.read) == ['cdent', 'fnd']
    assert ptwo.policy.write == ['cdent']

    STORE.delete(pone)

    ptwo = STORE.get(Recipe('ptwo'))

    assert sorted(ptwo.policy.read) == ['cdent', 'fnd']
    assert ptwo.policy.write == ['cdent']

    recipe = Recipe('pone')
    recipe.policy.read = [u'cdent']
    recipe.policy.write = [u'cdent']
    STORE.put(recipe)

    pone = STORE.get(Recipe('pone'))
    assert pone.policy.read == ['cdent']
    assert pone.policy.write == ['cdent']

    pone.policy.read.append(u'fnd')

    STORE.put(pone)

    pone = STORE.get(Recipe('pone'))

    assert sorted(pone.policy.read) == ['cdent', 'fnd']


def test_revisions_deletions():
    tiddler = Tiddler('tone', 'pone')
    tiddler.text = u'revision1'
    tiddler.tags = [u'1', u'2']
    STORE.put(tiddler)
    tiddler.text = u'revision2'
    tiddler.tags = [u'3', u'4']
    STORE.put(tiddler)

    revisions = STORE.list_tiddler_revisions(tiddler)

    assert len(revisions) == 2

    STORE.delete(tiddler)

    py.test.raises(NoTiddlerError, 'STORE.list_tiddler_revisions(tiddler)')


def test_bag_deletes_tiddlers():
    tiddler = Tiddler('tone', 'pone')
    STORE.put(tiddler)
    tiddler = Tiddler('uone', 'pone')
    STORE.put(tiddler)

    bag = Bag('pone')

    tiddlers = list(STORE.list_bag_tiddlers(bag))
    assert len(tiddlers) == 2

    STORE.delete(bag)

    bag = Bag('pone')
    py.test.raises(NoBagError, 'list(STORE.list_bag_tiddlers(bag))')
    py.test.raises(NoBagError, 'STORE.list_tiddler_revisions(tiddler)')


def test_saving_to_non_bag():
    tiddler = Tiddler('oh hi', 'nonexistentbag')
    py.test.raises(NoBagError, 'STORE.put(tiddler)')
