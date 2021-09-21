# P.A.P.E.R.

P.A.P.E.R. (Pablo's Artifacts and Papers Environment plus Repository)
helps keep track of metadata about what you read, breadcrumbs to find
it again. It helps with known-item search.

It contains:

* Data model: a hierarchical attribute-value pair DAG, completely
  contained in a YAML file.  BibTeX file + Mind Map You can define
  your own relations. It can be opened with any text editor, search
  inside of it, carry it in your phone, etc. It can be committed to
  version control.

* File repository: a digital assets manager that copies PDFs and
  other source paper files into a unified folder-balanced hash-based
  space in your file system.
  
* Search engine: for files in the paper file repository, the text is
  extracted and stored in an index that allows queries, including
  query-by-example, to find similar papers to existing ones.
  


## Features

* Exports to a static website.
* Imports BibTeX files.
* BibTeX generation.
* Imports from plain text files annotated with custom codes.
* Custom Jupyter widgets for editing and adding papers.
* Easy to hack, only 10 python files and 2000+ loc.



## Learning more

Take a look at the ``sample_notebooks`` folder for examples and the
``tests`` folder. The sample notebooks are rendered as HTML in https://drdub.github.io/PAPER/sample_notebooks/

There is also a ``docs`` folder containing known issues, a detailed model explanation and slides from talks about the tool.



## Install

```bash
virtualenv -p python3 /path/to/virtualenv/paperapp
source /path/to/virtualenv/paperapp/bin/activate
pip install -r requirements.txt
```

To use the development version then issue (from the root of this repository):

```bash
pip install -e .
```

To use Jupyter notebooks inside this virtual environment, you need to register before launching it:

```bash
python -m ipykernel install --user --name=paperapp
jupyter notebook
```

Alternatively, it can be installed from pip (test PyPI):

```bash
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps paperapp_DrDub
pip install paperapp_DrDub[widgets]
pip install paperapp_DrDub[fulltext]
```


## Acknowledgements

This tool got started at Les Laboratoires Foulab, Montreal's
hackerspace. It came up to speed for the writing of [The Art of
Feature Engineering](http://artoffeatureengineering.com/), where it
handled hundreds of references.
