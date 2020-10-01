import pytest
import os.path

from paperapp            import PaperError
from paperapp.paper_repo import PaperRepo

class TestRepo:

    def test_empty(self):
        p = PaperRepo()
        assert len(p.repo) == 0
        assert 'paper-1' not in p.id_to_node
        

    def test_load_no_types(self):
        p = PaperRepo(os.path.join(os.path.dirname(__file__),  'paper-no-types.yaml'))
        assert len(p.types) == len(PaperRepo.get_default_types())
        assert "".join(sorted(p.types.keys())) == "".join(sorted(PaperRepo.get_default_types()))

        assert p['paper-620']
        assert p['paper-620']['bibtex'] == p['fehlhaber2014hubel']
        assert p['paper-620']['related-to']['id'] == 'topic-cv'

        p['paper-620']['lecture'] = p.new_node(None, 'lecture', 'Test')
        with pytest.raises(PaperError):
            p.verify()

            
    def test_load_with_default_types(self):
        p = PaperRepo(os.path.join(os.path.dirname(__file__),  'paper-default-types.yaml'))
        assert len(p.types) == len(PaperRepo.get_default_types())
        assert "".join(sorted(p.types.keys())) == "".join(sorted(PaperRepo.get_default_types()))

        assert p['paper-620']
        assert p['paper-620']['bibtex'] == p['fehlhaber2014hubel']
        assert p['paper-620']['related-to']['id'] == 'topic-cv'

        
    def test_load_with_custom_types(self):
        p = PaperRepo(os.path.join(os.path.dirname(__file__),  'paper-custom-types.yaml'))
        assert len(p.types) != len(PaperRepo.get_default_types())
        assert "".join(sorted(p.types.keys())) != "".join(sorted(PaperRepo.get_default_types()))

        assert p['paper-620']
        assert p['paper-620']['bibtex'] == p['fehlhaber2014hubel']
        assert p['paper-620']['related-to']['id'] == 'topic-cv'
        assert p['paper-620']['lecture']['id'] == 'lecture-1'

        p['paper-620']['lecture'] = p.new_node(None, 'lecture', 'Test')
        p.verify()
        
    #TODO: test that functionality behaves well when a single object are multiple objects
