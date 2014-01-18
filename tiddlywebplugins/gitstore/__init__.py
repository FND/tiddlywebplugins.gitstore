"""
gitstore

TiddlyWeb store implementation using Git - based on the default text store, this
store uses Git to keep track of tiddler revisions
"""

import os
import time
import subprocess
import urllib

from datetime import datetime

from dulwich.repo import Repo
from dulwich.errors import NotGitRepository

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.serializer import TiddlerFormatError
from tiddlyweb.store import StoreLockError, NoBagError, NoTiddlerError
from tiddlyweb.stores.text import Store as TextStore, _encode_filename
from tiddlyweb.util import (binary_tiddler, LockError, write_lock, write_unlock,
        read_utf8_file, write_utf8_file)


class Store(TextStore):

    def __init__(self, store_config=None, environ=None):
        super(Store, self).__init__(store_config, environ)
        try:
            self.repo = Repo(self._root)
        except NotGitRepository:
            self.repo = Repo.init(self._root)

    def list_bag_tiddlers(self, bag):
        tiddlers_dir = self._tiddlers_dir(bag.name)

        try:
            tiddler_files = (filename for filename
                    in self._files_in_dir(tiddlers_dir)
                    if not filename == '.gitkeep')
        except (IOError, OSError), exc:
            raise NoBagError('unable to list tiddlers in bag "%s": %s' %
                    (bag.name, exc))

        bin_dir = os.path.basename(self._binaries_dir(bag.name))
        for filename in tiddler_files:
            if not filename == bin_dir:
                title = urllib.unquote(filename).decode('utf-8')
                yield Tiddler(title, bag.name)

    def list_tiddler_revisions(self, tiddler):
        tiddler_filename = self._tiddler_base_filename(tiddler)
        if not os.path.isfile(tiddler_filename):
            raise NoTiddlerError('unable to list revisions for tiddler "%s"'
                    % tiddler.title)

        try:
            relative_path = os.path.relpath(tiddler_filename, start=self._root)
            revisions = run('git', 'log', '--format=%H', '--', relative_path,
                    cwd=self._root) # TODO: should be handled via Dulwich
        except subprocess.CalledProcessError, exc:
            raise NoTiddlerError('unable to list revisions for tiddler "%s": %s'
                    % (tiddler.title, exc))

        return [rev[:10] for rev in revisions.splitlines()]

    def tiddler_get(self, tiddler): # XXX: prone to race condition due to separate Git operation
        tiddler_filename = self._tiddler_base_filename(tiddler)

        if tiddler.revision:
            return self._get_tiddler_revision(tiddler, tiddler_filename)

        try:
            tiddler = self._read_tiddler_file(tiddler, tiddler_filename)
        except IOError, exc:
            raise NoTiddlerError('no tiddler for "%s": %s' %
                    (tiddler.title, exc))

        relative_path = os.path.relpath(tiddler_filename, start=self._root)
        revision = run('git', 'log', '-n1', '--format=%H', '--', relative_path,
                cwd=self._root) # TODO: should be handled via Dulwich
        tiddler.revision = revision.strip()[:10]

        if binary_tiddler(tiddler):
            with open(self._binary_filename(tiddler), 'rb') as fh:
                tiddler.text = fh.read() # XXX: is it this simple?

        return tiddler

    def tiddler_put(self, tiddler):
        tiddler_filename = self._tiddler_base_filename(tiddler)
        bin_dir = self._binaries_dir(tiddler.bag)
        if tiddler_filename == bin_dir:
            raise TiddlerFormatError("reserved tiddler title")

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

        binary_data = None
        if binary_tiddler(tiddler):
            try:
                os.mkdir(bin_dir)
            except OSError, exc: # already exists
                pass
            binary_filename = self._binary_filename(tiddler)
            with open(binary_filename, 'wb') as fh:
                fh.write(tiddler.text) # XXX: is it this simple?
            binary_data = tiddler.text
            # ensure metadata file changes when binary contents change, thus
            # making it part of any commit - the metadata file is considered the
            # authoritative source for revisions
            tiddler.text = '~.~.~bincue~.~.~ %s' % datetime.now()

        write_utf8_file(tiddler_filename,
                self.serializer.serialization.tiddler_as(tiddler))
        write_unlock(tiddler_filename)

        commit_files = [tiddler_filename]

        if binary_data is not None:
            tiddler.text = binary_data # restore original
            commit_files.append(binary_filename)

        msg = 'tiddler put: %s/%s' % (tiddler.bag, tiddler.title)
        commit_id = self._commit(msg, *commit_files)
        tiddler.revision = commit_id[:10]

    def tiddler_delete(self, tiddler): # XXX: prone to race condition due to separate Git operation
        tiddler_filename = self._tiddler_base_filename(tiddler)
        if not os.path.exists(tiddler_filename):
            raise NoTiddlerError('%s not present' % tiddler_filename)

        os.remove(tiddler_filename)
        if binary_tiddler(tiddler):
            run('git', 'rm', self._binary_filename(tiddler), cwd=self._root) # TODO: should be handled via Dulwich

        msg = 'tiddler delete: %s/%s' % (tiddler.bag, tiddler.title)
        self._commit(msg, tiddler_filename)

    def bag_put(self, bag): # XXX: prone to race condition due to separate Git operation
        super(Store, self).bag_put(bag)

        bag_path = self._bag_path(bag.name)

        bag_files = self._bag_files(bag_path)
        keepfile = bag_files[-1]
        with file(keepfile, 'a'):
            os.utime(keepfile, None) # `touch`

        self._commit('bag put: %s' % bag.name, *bag_files)

    def bag_delete(self, bag): # XXX: prone to race condition due to separate Git operation
        super(Store, self).bag_delete(bag)

        bag_path = self._bag_path(bag.name)
        self._commit('bag delete: %s' % bag.name, *self._bag_files(bag_path))

    def recipe_put(self, recipe): # XXX: prone to race condition due to separate Git operation
        super(Store, self).recipe_put(recipe)

        recipe_filename = self._recipe_path(recipe)
        self._commit('recipe put: %s' % recipe.name, recipe_filename)

    def recipe_delete(self, recipe): # XXX: prone to race condition due to separate Git operation
        super(Store, self).recipe_delete(recipe)

        recipe_filename = self._recipe_path(recipe)
        self._commit('recipe delete: %s' % recipe.name, recipe_filename)

    def user_put(self, user): # XXX: prone to race condition due to separate Git operation
        super(Store, self).user_put(user)

        user_filename = self._user_path(user)
        self._commit('user put: %s' % user.usersign, user_filename)

    def user_delete(self, user): # XXX: prone to race condition due to separate Git operation
        super(Store, self).user_delete(user)

        user_filename = self._user_path(user)
        self._commit('user delete: %s' % user.usersign, user_filename)

    def search(self, search_query):
        raise NotImplementedError

    def _get_tiddler_revision(self, tiddler, tiddler_filename):
        relative_path = os.path.relpath(tiddler_filename, start=self._root)
        target = '%s:%s' % (tiddler.revision, relative_path)
        try:
            tiddler_string = run('git', 'show', target, cwd=self._root) # TODO: should be handled via Dulwich
        except subprocess.CalledProcessError, exc:
            raise NoTiddlerError('no revision %s for %s: %s' %
                    (tiddler.revision, tiddler.title, exc))

        revision_tiddler = Tiddler(tiddler.title, tiddler.bag)
        self.serializer.object = revision_tiddler
        self.serializer.from_string(tiddler_string)
        revision_tiddler.revision = tiddler.revision
        revision_tiddler.recipe = tiddler.recipe
        return revision_tiddler

    def _commit(self, message, *filenames):
        """
        commit changes to given files

        returns the new commit's hash
        """
        host = self.environ['tiddlyweb.config']['server_host']
        host = '%s:%s' % (host['host'], host['port'])
        if host.endswith(':80'): # TODO: use proper URI parsing instead
            host = host[:-3]
        user = self.environ.get('tiddlyweb.usersign', {}).get('name', None)
        author = '%s <%s@%s>' % (user, user, host)
        committer = 'tiddlyweb <tiddlyweb@%s>' % host

        for filepath in filenames:
            relpath = os.path.relpath(filepath, start=self._root)
            self.repo.stage([relpath])
        return self.repo.do_commit(message.encode("UTF-8"), author=author,
                committer=committer)

    def _bag_files(self, bag_path):
        bag_files = ['description', 'policy',
                os.path.join('tiddlers', '.gitkeep')]
        return [os.path.join(bag_path, filename) for filename in bag_files]

    def _binaries_dir(self, bag_name):
        return os.path.join(self._tiddlers_dir(bag_name), '_binaries')

    def _binary_filename(self, tiddler):
        return os.path.join(self._binaries_dir(tiddler.bag),
                _encode_filename(tiddler.title))


def run(cmd, *args, **kwargs):
    """
    execute a command, passing `args` to that command and using `kwargs` for
    configuration of `Popen`, returning the respective output
    """
    args = [cmd] + list(args)
    return subprocess.check_output(args, **kwargs)
