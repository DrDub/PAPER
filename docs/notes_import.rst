=============================
Importing notes into the tool
=============================

code2py
-------

To streamline the process of maintaining and uploading notes, it is
possible to enhance plain text notes with codes to be uploaded into
the tool.

The format is:

Each entry starts with 'p<unique number>'. A number of fields follows,
each started with a field code:

E a URL to be used for the 'external' entry
O a file on disk to be used for the 'on-disk' entry
T the title entry (title and authors, etc, it is the 'text' entry of the node)
S status, one of 'read', 'read-abstract', 'unread', 'skimmed', etc
R when and where it was read
F when and how it was found

Everything else becomes the note for the paper.

The resulting output is a python code that can be further edited and
executed in a Jupyter notebook.
