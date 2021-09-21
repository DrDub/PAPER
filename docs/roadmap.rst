=======
Roadmap
=======

Here are some potential improvements.

Context manager
---------------

Allow to specify ``with PaperRepo(...) as p:``

Sync-tool
---------

Folder with PDFs vs. .bib file sync tool.

JQuery-like functionality
-------------------------

As links in the model can be either single elements or lists of elements, accessing a path in the graph should return all the elements reachable by that path.

For example ``p['paper-620']['note']`` can return either a string or list of strings, depending if there is one note or multiple notes.

Now, issuing ``p['paper-620']['related-to']['text']`` to find the titles of topics related to the paper will only work if it is one topic related.

A functionality where we can issue ``p.lget("paper-620/related-to/text")`` and return an iterator will be handy.

