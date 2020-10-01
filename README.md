# P.A.P.E.R. (Pablo's Artifacts and Papers Environment plus Repository)

## Install

```bash
virtualenv -p python3 /path/to/virtualenv/paperapp
source /path/to/virtualenv/paperapp/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name=paperapp
jupyter notebook
```

For use of the full text search, you might need to install the Debian
package 'libpoppler-cpp-dev'.

From pip:

```bash
pip install paperapp[widgets]
pip install paperapp[fulltext]
```
