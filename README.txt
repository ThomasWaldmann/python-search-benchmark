A simple python search library benchmark
========================================

Supporting:
 * whoosh (a search library in pure Python)
 * xappy / xapian (Python + C++)

How it benchmarks
-----------------
First, we create a list of documents that are used for all the benchmarks
(it uses exactly the same list of the same documents for all, of course).

The documents contain some random word, the word length, and some extra fields
to pump up the size of the document (you can create quite large indexes that
way).

Then we create an index for these documents, all fields are indexed/stored.

Then we search the index for all words in random order and read all stored
fields for the search results.

Notes
-----
For whoosh indexing, there is a USE_MULTIPROCESSING setting.
When using True, keep in mind that it could be not quite fair (as other
indexers maybe don't use multiple cores / processes). But OTOH, if it
is that easy, why not use it? :)

To make the Xapian install as simple as possible its recommended that you put
the xapian-core and xapian-bindings into the same virtualenv which hosts these
benchmarks. To help we've included a shell script which will attempt to set
these up for you.
