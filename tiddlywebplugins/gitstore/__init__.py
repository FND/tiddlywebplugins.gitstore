"""
Git Store
TiddlyWeb store implementation using Git - based on the default text store, this
store uses Git to keep track of tiddler revisions
"""

from dulwich.repo import Repo
from dulwich.errors import NotGitRepository

from tiddlyweb.stores.text import Store as TextStore


class Store(TextStore):

    def __init__(self, store_config=None, environ=None):
        super(Store, self).__init__(store_config, environ)
        try:
            self.repo = Repo(self._root)
        except NotGitRepository:
            self.repo = Repo.init(self._root)
