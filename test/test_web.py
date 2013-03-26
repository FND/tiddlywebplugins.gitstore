from __future__ import absolute_import

import httplib2

from tiddlyweb.model.bag import Bag

from . import initialize_app, store_setup, store_teardown


def setup_module(module):
    module.STORE, module.TMPDIR = store_setup()
    cfg = initialize_app(module.STORE.environ['tiddlyweb.config'])

    module.STORE.put(Bag('alpha'))


def teardown_module(module):
    store_teardown(module.TMPDIR)


def test_lifecycle():
    bag = 'alpha'

    # create and remove

    title = 'HelloWorld'

    response = _put_tiddler(title, bag, 'lorem ipsum')
    assert response.status == 204
    etag = response['etag']

    response, content = _get_tiddler(title, bag)
    assert response.status == 200
    assert response['etag'].split(':')[0] == etag.split(':')[0]
    assert content.endswith('\n\nlorem ipsum\n')

    response = _delete_tiddler(title, bag, etag)
    assert response.status == 204

    # create and modify

    title = 'Lipsum'

    response = _put_tiddler(title, bag, 'lorem ipsum')
    assert response.status == 204
    etag = response['etag']

    response, content = _get_tiddler(title, bag)
    assert response.status == 200
    assert response['etag'].split(':')[0] == etag.split(':')[0]
    assert content.endswith('\n\nlorem ipsum\n')

    response = _put_tiddler(title, bag, 'lorem ipsum\ndolor sit amet')
    assert response.status == 204
    etag = response['etag']

    response, content = _get_tiddler(title, bag)
    assert response.status == 200
    assert response['etag'].split(':')[0] == etag.split(':')[0]
    assert content.endswith('\n\nlorem ipsum\ndolor sit amet\n')

    # create, create, delete

    title = 'Foo'

    response = _put_tiddler(title, bag, 'lorem ipsum')
    assert response.status == 204
    etag_put = response['etag']

    response, content = _get_tiddler(title, bag)
    assert response.status == 200
    assert response['etag'].split(':')[0] == etag_put.split(':')[0]
    assert content.endswith('\n\nlorem ipsum\n')

    # create unrelated tiddler
    response = _put_tiddler('Bar', bag, 'lorem ipsum')
    assert response.status == 204

    response = _delete_tiddler(title, bag, etag_put)
    assert response.status == 204



def _get_tiddler(title, bag):
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)

    http = httplib2.Http()
    response, content = http.request(uri, method='GET',
            headers={ 'Accept': 'text/plain' })

    return response, content


def _put_tiddler(title, bag, body):
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)
    rep = 'tags: \n\n%s' % body

    http = httplib2.Http()
    response, content = http.request(uri, method='PUT',
            headers={ 'Content-Type': 'text/plain' }, body=rep)

    return response


def _delete_tiddler(title, bag, etag=None):
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)

    http = httplib2.Http()
    headers = { 'If-Match': etag } if etag else None
    response, content = http.request(uri, method='DELETE', headers=headers)

    return response
