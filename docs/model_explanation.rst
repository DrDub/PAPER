================================================
Explanation for the entries in the default model
================================================

What do the entries mean?
=========================

The default entries make sense (sometimes) to the author but most
probably you would want to customize them. Note that certain
functionality is tied to the entries keeping these names.

Explanation by node type
========================

Here is an explanation by node type, starting by 'artifact' the most
important type of node.

All entries can take a string as value or a list of the items
described below. The lists are ordered by importance.

artifact
--------

id
  All nodes have a unique ID.

title
  A piece of text representing the node. Only mandatory field.

status
  A string indicating whether the paper is unread, read, skimmed. These values are understood by the reading list manager.

topic
  One or more "topic" nodes or a string describing them.

bibtex
  Entry of type "bibtex" of the full bibtex as a string. The bibtex exporter only works with links to bibtex nodes.

found-in
  How the paper was found. It could be a free text, another "artifact" node, an "external" source of a "search" node.

found-date
  Date when the paper was found.

read
  When and where the paper was read. Multiple entries indicate multiple reading sessions. A "scenario" node can be used to split time and location.

on-disk
  This is the link to the file repository through a "file" node, but a string can be supplied to point to where the file lives.

external
   For artifacts living in the cloud, "external" node allows to describe their location.

