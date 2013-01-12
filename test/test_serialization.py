from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.serializations.text import Serialization as TextSerialization

from tiddlywebplugins.gitstore.serializer import FullTextSerializer


def test_tiddler_representation():
    tiddler = Tiddler('Foo')
    tiddler.creator = 'john'
    tiddler.text = 'lorem ipsum\ndolor sit amet'

    representation = TextSerialization().tiddler_as(tiddler)
    assert 'creator: ' not in representation
    assert '\n\nlorem ipsum\ndolor sit amet' in representation

    representation = FullTextSerializer().tiddler_as(tiddler)
    assert 'creator: john\n' in representation
    assert '\n\nlorem ipsum\ndolor sit amet' in representation
