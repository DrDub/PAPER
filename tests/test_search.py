import pytest
import tempfile
import os.path

from paperapp              import PaperError
from paperapp.paper_repo   import PaperRepo
from paperapp.paper_bibtex import import_bibtex, import_bibtex_str


class TestSearch:
    def test_search(self):
        with tempfile.TemporaryDirectory("pytest") as data_folder:
            p = PaperRepo(data_folder=data_folder, auto_save=True)
            ids = import_bibtex(p, os.path.join(os.path.dirname(__file__),  'duboue.bib'), verbose=False, create_papers=True)

            bib_to_paper = {}
            for paper_id in ids:
                paper = p[paper_id]
                bib_to_paper[paper['bibtex']['id']] = paper

            for entry, fname in [ ( 'duboue2019dialect', 'CLEI2019dialect.pdf' ),
                                  ( 'ying-duboue-2019-rationale', 'W19-5503.pdf' ),
                                  ( 'duboue2018choice', 'ASAI2018choice.pdf' ),
                                  ( 'Duboue_al_2013' , '05-NTCIR10-1CLICK-PabloD.pdf' ),
                                  ( 'duboue_2013_ENLG2', 'W13-2129.pdf' ),
                                  ( 'Jing_al_12', 'C12-1069.pdf' ),
                                  ( 'Pacheco_al_12', 'N12-1082.pdf' ),
                                  ( 'Duboue_12', 'INLG2012duboue.pdf' ),
                                  ( 'Ferrucci_al_08', 'rc24789.pdf' ),
                                  ( 'Duboue_Chu-Carrol_06', 'N06-2009.pdf' ),
                                  ( 'Prager_al_06', 'P06-1135.pdf' ),
                                  ( 'Duboue_McKeown_03a', 'W03-1016.pdf' ),
                                  ( 'Costa_Duboue_04', 'ASAI04distributed.pdf' ),
                                  ( 'Hatzivassiloglou_al_01a', 'ISMB2001disambiguation.pdf' ) ]:
                bib_to_paper[entry]['on-disk'] = p.register_file(os.path.join(os.path.dirname(__file__), fname))

            # things that are supposed to be there are there
            assert p.text(bib_to_paper['Ferrucci_al_08']['id'])
            start="RC24789 (W0904-093) April 22, 2009\nComputer Science\n                       IBM Research Report\n             Towards the Open Advancement of Question\n                                    Answering Systems\n   David Ferrucci1, Eric Nyberg2, James Allan3, Ken Barker4, Eric Brown1,\n     Jennifer Chu-Carroll1, Arthur Ciccolo1, Pablo Duboue1, James Fan1,\n David Gondek1, Eduard Hovy5, Boris Katz6, Adam Lally1, Michael McCord1,\n         Paul Morarescu1, Bill Murdock1, Bruce Porter4, John Prager1,\n        "
            assert p.text(bib_to_paper['Ferrucci_al_08']['id'])[:len(start)] == start
            #print(repr(p.text(bib_to_paper['Ferrucci_al_08']['id'])[:500]))
                
            # things without text are not there
            with pytest.raises(PaperError):
                p.text(bib_to_paper['duboue2020art']['id'])

            # add a non-PDF entry
            pptx = p.new_paper(None, '2018 lighting talk', on_disk=p.register_file(os.path.join(os.path.dirname(__file__), '201811_lds_lighting_duboue.pptx')))

            # text is there
            start = """My textbook story: what, why and how

What: a textbook on Feature Engineering

	

The Art of Feature Engineering: Essentials for Machine Learning

	

Coming in 2019, Cambridge University Press

Sharing my personal story

	

Meet more people in Vancouver

	

Encouraging others to write
"""
            assert p.text(pptx['id'])
            assert p.text(pptx['id'])[:len(start)] == start

            # another non-PDF entry
            html = p.new_paper(None, '2018 lighting talk - html', on_disk=p.register_file(os.path.join(os.path.dirname(__file__), '201811_lds_lighting_duboue.html')))
            assert p.text(html['id'])
            start = """
Next 'div' was a 'draw:text-box'.

My textbook story: what, why and how

Next 'div' was a 'draw:text-box'.

What: a textbook on Feature Engineering

The Art of Feature Engineering: Essentials for Machine Learning

Coming in 2019, Cambridge University Press

Sharing my personal story

"""
            assert p.text(html['id'])[:len(start)] == start
                        
            results = p.search("generation AND NOT statistical")
            assert len(results) == 8
            assert results[0]['paper']['text'] == 'On The Feasibility of Open Domain Referring Expression Generation Using Large Scale Folksonomies -- Pacheco, Fabian  and  Duboue, Pablo  and  Dominguez, Martin'
