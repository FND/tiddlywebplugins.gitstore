"""
Git Store
TiddlyWeb store implementation using Git - based on the default text store, this
store uses Git to keep track of tiddler revisions.
"""

from dulwich.repo import Repo

from tiddlyweb.stores.text import Store as TextStore


class Store(TextStore):

    def __init__(self, store_config=None, environ=None):
        super(Store, self).__init__(store_config, environ)
        Repo.init(self._root)
