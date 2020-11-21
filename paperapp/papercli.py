import sys

from .paper_repo   import PaperRepo
from .materializer import materialize
from .paper_bibtex import generate_bibtex
from .code2py      import process_lines


def cli():
    if len(sys.argv) < 2:
        code = ""
    else:
        code = sys.argv[1]
    if code == 'materialize':
        p = PaperRepo(sys.argv[2], sys.argv[3])
        materialize(p, sys.argv[4])
    elif code == 'bibtex':
        p = PaperRepo(sys.argv[2], sys.argv[3])
        generate_bibtex(p, sys.argv[4])
    elif code == 'code2py':
        print("\n".join(process_lines(sys.stdin, render=True)))
    else:
        print("""papercli usage:

  papercli materialize yaml filerepo target

  papercli bibtex yaml filerepo citingrel

  papercly code2py < notes
""")

