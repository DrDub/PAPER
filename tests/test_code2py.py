import pytest
import tempfile
import os.path

from paperapp              import PaperError
from paperapp.paper_repo   import PaperRepo
from paperapp.code2py      import process_lines
from paperapp.paper_bibtex import import_bibtex, import_bibtex_str


class TestCode2py:

    def test_upload(self):
        text="""p1

E http://www.duboue.net/pablo/papers/CLEI2019dialect.pdf
T Impact of Spanish Dialect in Deep Learning Next Sentence Predictors -- Duboue -- 2019
F 20200930 LearnDS lighting talk prep
S own-paper
O CLEI2019dialect.pdf

This paper describes using BERT to quantify differences between Spanish dialects. 
It works with the parliamentary proceedings of Argentina and Costa Rica.


p2
E https://www.aclweb.org/anthology/W19-5503
T Rationale Classification for Educational Trading Platforms -- Ying, Duboue -- 2019
F 20200930 LearnDS lighting talk prep
S own-paper
O W19-5503.pdf

Multi-task learning to tell apart comments like "here comes a winner"
(that carry no semantic content) vs. "the new announcement from
the feds mean resource extraction should start gaining ground
now."

p3
E http://www.duboue.net/pablo/papers/ASAI2018choice.pdf
T Deobfuscating Name Scrambling as a Natural Language Generation Task -- Duboue -- 2019
S own-paper

Journal version of the ASAI paper. Used RF to predict the main keyword
in a Java method, from bytecodes as features.
"""
        lines = process_lines(text.split("\n"), file_folder=os.path.dirname(__file__))
        print("\n".join(lines))
        assert len(lines) == 25

        with tempfile.TemporaryDirectory("pytest") as data_folder:
            p = PaperRepo(data_folder=data_folder, auto_save=True)
            exec("\n".join(lines) + "\n")
            
            assert locals()['p1']['id'] == "paper-1"
            assert locals()['p2']['on-disk']['text'] == "W19-5503.pdf"
            assert locals()['p3']['text'] == p['paper-3']['text']
            assert p.text(p['paper-1']['id'])

            
        
        
