import pytest
import os.path

from paperapp              import PaperError
from paperapp.paper_repo   import PaperRepo
from paperapp.paper_bibtex import import_bibtex, import_bibtex_str

class TestBibtex:

    def test_import(self):
        p = PaperRepo()
        ids = import_bibtex(p, os.path.join(os.path.dirname(__file__),  'duboue.bib'), verbose=True)
        assert len(ids) == 44
        print(ids)
        assert 'duboue2020art' in ids


    def test_parse_error(self):
        
        p = PaperRepo()
        with pytest.raises(PaperError):
            # missing a comma
            ids = import_bibtex_str(p, """
@book{duboue2020art,
  title={The Art of Feature Engineering: Essentials for Machine Learning},
  author={Duboue, Pablo},
  year={2020},
  month={June},
  isbn={978-1108709385}
  publisher={Cambridge University Press},
  url={http://artoffeatureengineering.com}
}
""")

        
