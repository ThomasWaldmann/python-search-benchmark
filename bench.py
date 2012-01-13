# Copyright: 2011 MoinMoin:ThomasWaldmann
# License: MIT licensed
"""
A simple python search library benchmark.

We just index all words and their lengths from the dict file.

Afterwards we search the index for all words in random order
and read the stored fields (== the word and its length).

Supporting:
 * whoosh
 * xappy / xapian

Note: for whoosh indexing, there is a USE_MULTIPROCESSING setting.
When using True, keep in mind that it could be not quite fair (as other
indexers maybe don't use multiple cores / processes). But OTOH, if it
is that easy, why not use it? :)
"""

import codecs
import os
import shutil
import random
import time

DICT_FILE = '/usr/share/dict/american-english'
WORD_COUNT = 10000

# prepare data, so this doesn't go into timings:
with codecs.open(DICT_FILE, 'r', 'utf-8') as f:
    WORDS = f.read().split(u'\n')

WORDS = WORDS[:WORD_COUNT]
WORD_COUNT = len(WORDS)

SHUFFLED_WORDS = WORDS[:]
random.shuffle(SHUFFLED_WORDS)


class Bench(object):
    def __init__(self, index_dir):
        self.index_dir = index_dir

    def remove_index(self):
        shutil.rmtree(self.index_dir)

    def bench(self, func):
        t_start = time.time()
        func()
        t_end = time.time()
        return t_end - t_start

    def bench_all(self):
        print "Benchmarking: %s" % self.NAME
        t_index = self.bench(self.create_index)
        print "Indexing %d words takes %.1fs (%.1f/s)" % (WORD_COUNT, t_index, WORD_COUNT/t_index)
        t_search = self.bench(self.search)
        print "Searching %d words takes %.1fs (%.1f/s)" % (WORD_COUNT, t_search, WORD_COUNT/t_search)
        print
        self.remove_index()


import whoosh
from whoosh.fields import Schema, ID, NUMERIC
from whoosh.index import open_dir, create_in
from whoosh.filedb.multiproc import MultiSegmentWriter
from whoosh.query import Term


class Whoosh(Bench):
    NAME = 'whoosh %d.%d.%d' % whoosh.__version__
    USE_MULTIPROCESSING = True

    def make_docs(self):
        for word in WORDS:
            yield {'word': word, 'length': len(word), }

    def create_index(self):
        schema = Schema(
            word=ID(stored=True),
            length=NUMERIC(stored=True),
        )
        os.mkdir(self.index_dir)
        ix = create_in(self.index_dir, schema)
        if self.USE_MULTIPROCESSING:
            writer = MultiSegmentWriter(ix, limitmb=128)
        else:
            writer = ix.writer(limitmb=256)
        with writer as writer:
            for doc in self.make_docs():
                writer.add_document(**doc)
        ix.close()

    def search(self):
        ix = open_dir(self.index_dir)
        with ix.searcher() as searcher:
            for word in SHUFFLED_WORDS:
                query = Term('word', word)
                results = searcher.search(query, limit=1)
                for result in results:
                    # make sure to really read the stored fields
                    dummy = repr(result.fields())


import xapian
import xappy
from xappy import IndexerConnection, SearchConnection, \
                  FieldActions, UnprocessedDocument


class Xappy(Bench):
    NAME = 'xappy %s / xapian %d.%d.%d' % (xappy.__version__,
                                           xapian.major_version(), xapian.minor_version(), xapian.revision(), )

    def make_docs(self):
        for word in WORDS:
            # note: xappy doesn't like int
            yield {'word': word, 'length': unicode(len(word)), }

    def create_index(self):
        iconn = IndexerConnection(self.index_dir)
        iconn.add_field_action('word', FieldActions.STORE_CONTENT)
        iconn.add_field_action('word', FieldActions.INDEX_EXACT)
        iconn.add_field_action('length', FieldActions.STORE_CONTENT)
        iconn.add_field_action('length', FieldActions.INDEX_EXACT)
        iconn.close()
        iconn = IndexerConnection(self.index_dir)
        for doc in self.make_docs():
            xappy_doc = UnprocessedDocument()
            for k, v in doc.items():
                xappy_doc.fields.append(xappy.Field(k, v))
            iconn.add(xappy_doc)
        iconn.flush()
        iconn.close()

    def search(self):
        sconn = SearchConnection(self.index_dir)
        for word in SHUFFLED_WORDS:
            query = sconn.query_field('word', word)
            results = sconn.search(query, 0, 1)
            for result in results:
                # make sure to really read the stored fields
                dummy = repr(result.data)
        sconn.close()


if __name__ == '__main__':
    Xappy('xapian_ix').bench_all()
    Whoosh('whoosh_ix').bench_all()

