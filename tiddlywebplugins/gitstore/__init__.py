"""
Git Store
TiddlyWeb store implementation using Git - based on the default text store, this
store uses Git to keep track of tiddler revisions
"""

import os
import time
import subprocess

from dulwich.repo import Repo
from dulwich.errors import NotGitRepository

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.store import StoreLockError, NoTiddlerError
from tiddlyweb.stores.text import Store as TextStore
from tiddlyweb.util import LockError, write_lock, write_unlock, \
        read_utf8_file, write_utf8_file

from .serializer import FullTextSerializer


class Store(TextStore):

    def __init__(self, store_config=None, environ=None):
        super(Store, self).__init__(store_config, environ)
        try:
            self.repo = Repo(self._root)
        except NotGitRepository:
            self.repo = Repo.init(self._root)

    def tiddler_get(self, tiddler): # XXX: prone to race condition due to separate Git operation
        tiddler_filename = self._tiddler_base_filename(tiddler)

        if tiddler.revision:
            return self._get_tiddler_revision(tiddler, tiddler_filename)

        try:
            tiddler = self._read_tiddler_file(tiddler, tiddler_filename)
        except IOError, exc:
            raise NoTiddlerError('no tiddler for %s: %s' % (tiddler.title, exc))

        revision = run('git', 'log', '-n1', '--format=%H', cwd=self._root) # TODO: should be handled via Dulwich
        tiddler.revision = revision.strip()

        return tiddler

    def tiddler_put(self, tiddler):
        tiddler_filename = self._tiddler_base_filename(tiddler)

        # the following section is copied almost verbatim from the text store
        # TODO: refactor the text store for granular reusability
        locked = 0
        lock_attempts = 0
        while not locked:
            try:
                lock_attempts = lock_attempts + 1
                write_lock(tiddler_filename)
                locked = 1
            except LockError, exc:
                if lock_attempts > 4:
                    raise StoreLockError(exc)
                time.sleep(.1)

        # Protect against incoming tiddlers that have revision set. Since we are
        # putting a new one, we want the system to calculate.
        tiddler.revision = None

        # store original creator and created
        try:
            current_rev = Tiddler(tiddler.title, tiddler.bag)
            current_rev = self._read_tiddler_file(current_rev, tiddler_filename)
            tiddler.creator = current_rev.creator
            tiddler.created = current_rev.created
        except IOError, exc: # first revision
            tiddler.creator = tiddler.modifier
            tiddler.created = tiddler.modified

        write_utf8_file(tiddler_filename,
                FullTextSerializer().tiddler_as(tiddler))
        write_unlock(tiddler_filename)

        commit_id = self._commit(tiddler_filename, 'tiddler put') # XXX: message too technical?
        tiddler.revision = commit_id # TODO: use abbreviated commit hash

    def tiddler_delete(self, tiddler): # XXX: prone to race condition due to separate Git operation
        tiddler_filename = self._tiddler_base_filename(tiddler)
        if not os.path.exists(tiddler_filename):
            raise NoTiddlerError('%s not present' % tiddler_filename)

        os.remove(tiddler_filename)

        self._commit(tiddler_filename, 'tiddler delete') # XXX: message too technical?


    def _get_tiddler_revision(self, tiddler, tiddler_filename):
        relative_path = os.path.relpath(tiddler_filename, start=self._root)
        target = '%s:%s' % (tiddler.revision, relative_path)
        try:
            tiddler_string = run('git', 'show', target, cwd=self._root) # TODO: should be handled via Dulwich
        except subprocess.CalledProcessError, exc:
            raise NoTiddlerError('no revision %s for %s: %s' %
                    (tiddler.revision, tiddler.title, exc))

        self.serializer.object = Tiddler(tiddler.title, tiddler.bag)
        return self.serializer.from_string(tiddler_string)

    def _commit(self, filename, message):
        """
        commit changes to given file

        returns the new commit's hash
        """
        host = self.environ['tiddlyweb.config']['server_host']
        host = '%s:%s' % (host['host'], host['port'])
        if host.endswith(':80'): # TODO: use proper URI parsing instead
            host = host[:-3]
        user = self.environ['tiddlyweb.usersign']['name']
        author = '%s <%s@%s>' % (user, user, host)
        committer = 'tiddlyweb <tiddlyweb@%s>' % host

        relative_path = os.path.relpath(filename, start=self._root)
        self.repo.stage([relative_path])
        return self.repo.do_commit(message, author=author, committer=committer)


def run(cmd, *args, **kwargs):
    """
    execute a command, passing `args` to that command and using `kwargs` for
    configuration of `Popen`, returning the respective output
    """
    args = [cmd] + list(args)
    return subprocess.check_output(args, **kwargs)
