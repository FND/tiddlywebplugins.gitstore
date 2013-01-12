from tiddlyweb.model.tiddler import Tiddler

from tiddlyweb.serializations.text import Serialization as TextSerialization


class FullTextSerializer(TextSerialization): # XXX: bad name

    def tiddler_as(self, tiddler):
        """
        include creator in serialization
        """
        text = super(FullTextSerializer, self).tiddler_as(tiddler)
        return 'creator: %s\n%s' % (tiddler.creator, text)
