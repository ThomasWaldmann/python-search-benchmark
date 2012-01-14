# -*- coding: utf-8 -*-
# Copyright: 2011 MoinMoin:ThomasWaldmann
# License: MIT licensed
"""
A simple python search library benchmark
"""

import codecs
import os
import shutil
from random import choice, shuffle, randint
import time

DOC_COUNT = 3000 # how many documents do we index (same count for search)
COMPLEX_COUNT = 300 # how many complex searches to run
WORD_LEN = 10 # word length we put into index and also search for

# these are just extra fields to make the indexed documents bigger,
# they are just stored and indexed, but not used for searching:
EXTRA_FIELD_COUNT = 10
EXTRA_FIELD_LEN = 100
EXTRA_FIELDS = ["f%d" % i for i in xrange(EXTRA_FIELD_COUNT)]


def generate_word(length):
    chars = list(u"abcdefghijklmnopqrstuvwxyz" +
                 u"ABCDEFGHIJKLMNOPQRSTUVWXYZ" +
                 u"äöüÄÖÜß")
    r = xrange(length)
    word = u''.join(choice(chars) for i in r)
    return word


def generate_data():
    # prepare data, so this doesn't go into timings:
    global DOC_COUNT, WORDS, SHUFFLED_WORDS, DOCS
    print "Params:"
    print "DOC_COUNT: %d WORD_LEN: %d" % (DOC_COUNT, WORD_LEN)
    print "EXTRA_FIELD_COUNT: %d EXTRA_FIELD_LEN: %d" % (EXTRA_FIELD_COUNT, EXTRA_FIELD_LEN)
    print
    WORDS = set() # make sure words are unique
    while len(WORDS) < DOC_COUNT:
        WORDS.add(generate_word(WORD_LEN))
    WORDS = list(WORDS)
    SHUFFLED_WORDS = WORDS[:]
    shuffle(SHUFFLED_WORDS)
    DOCS = []
    for w in WORDS:
        doc = {}
        doc['word'] = w
        doc['two'] = unicode(randint(0, 1))
        doc['four'] = unicode(randint(0, 3))
        doc['eight'] = unicode(randint(0, 7))
        for field in EXTRA_FIELDS:
            doc[field] = generate_word(EXTRA_FIELD_LEN)
        DOCS.append(doc)


class Bench(object):
    def __init__(self, index_dir):
        self.index_dir = index_dir

    def remove_index(self):
        shutil.rmtree(self.index_dir)

    def make_docs(self):
        for doc in DOCS:
            yield doc

    def bench(self, func):
        t_start = time.time()
        func()
        t_end = time.time()
        return t_end - t_start

    def bench_all(self):
        print "Benchmarking: %s" % self.NAME
        t_index = self.bench(self.create_index)
        print "Indexing takes %.1fs (%.1f/s)" % (t_index, DOC_COUNT/t_index)
        t_search = self.bench(self.search)
        print "Searching takes %.1fs (%.1f/s)" % (t_search, DOC_COUNT/t_search)
        t_search_complex = self.bench(self.search_complex)
        print "Complex Searching takes %.1fs (%.1f/s)" % (t_search_complex, COMPLEX_COUNT/t_search_complex)
        print
        self.remove_index()


try:
    import whoosh
    from whoosh.fields import Schema, ID, NUMERIC
    from whoosh.index import open_dir, create_in
    from whoosh.filedb.multiproc import MultiSegmentWriter
    from whoosh.query import Term, And
except ImportError:
    whoosh = None

if whoosh:
    class Whoosh(Bench):
        NAME = 'whoosh %d.%d.%d' % whoosh.__version__
        USE_MULTIPROCESSING = True

        def create_index(self):
            fields = {}
            for field in ['word', 'two', 'four', 'eight', ] + EXTRA_FIELDS:
                fields[field] = ID(stored=True)
            schema = Schema(**fields)
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

        def search_complex(self):
            ix = open_dir(self.index_dir)
            with ix.searcher() as searcher:
                query = And([Term('two', '1'),
                             Term('four', '2'),
                             Term('eight', '3')])
                for i in xrange(COMPLEX_COUNT):
                    results = searcher.search(query, limit=10)
                    for result in results:
                        # make sure to really read the stored fields
                        dummy = repr(result.fields())

try:
    import xapian
    from xapian import Query
    import xappy
    from xappy import IndexerConnection, SearchConnection, \
                      FieldActions, UnprocessedDocument
except ImportError:
    xapian = None

if xapian:
    class Xappy(Bench):
        NAME = 'xappy %s / xapian %d.%d.%d' % (xappy.__version__,
                                               xapian.major_version(), xapian.minor_version(), xapian.revision(), )

        def create_index(self):
            iconn = IndexerConnection(self.index_dir)
            for field in ['word', 'two', 'four', 'eight', ] + EXTRA_FIELDS:
                iconn.add_field_action(field, FieldActions.STORE_CONTENT)
                iconn.add_field_action(field, FieldActions.INDEX_EXACT)
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

        def search_complex(self):
            sconn = SearchConnection(self.index_dir)
            terms = [
                sconn.query_field('two', '1'),
                sconn.query_field('four', '2'),
                sconn.query_field('eight', '3'),
            ]
            query = Query(Query.OP_AND, terms)
            for i in xrange(COMPLEX_COUNT):
                results = sconn.search(query, 0, 10)
                for result in results:
                    # make sure to really read the stored fields
                    dummy = repr(result.data)
            sconn.close()

if __name__ == '__main__':
    generate_data()
    if xapian:
        Xappy('xapian_ix').bench_all()
    if whoosh:
        Whoosh('whoosh_ix').bench_all()

