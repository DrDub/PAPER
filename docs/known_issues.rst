============
Known Issues
============

Links in render_node are not clickable
--------------------------------------

``render_node`` in ``paper_ipython.py`` uses the templates from
``materializer.py``. As such, it does not produce links that work. A
better solution would rewrite it using widgets and have live buttons
to go from node to node.

Search is only for full-text, no notes search at the moment
-----------------------------------------------------------

Searching within notes can be done too easily by opening the YAML file
in a text editor. If anybody needs or wants a search functionality,
open a ticket and let's talk about it.


Problems with "Any entry can be a string or a list"
---------------------------------------------------

The idea that every entry in the nodes can be a string or a list of
nodes of the mandated types is not currently 100% functional. Many
places in the code assume is only one node. More test cases should
help root out these bugs.
