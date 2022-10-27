import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="paperapp-DrDub",
    version="0.0.2",
    author="Pablo Duboue",
    author_email="pablo.duboue@gmail.com",
    description="Artifacts and Papers Environment plus Repository",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DrDub/PAPER",
    packages=setuptools.find_packages(),
    keywords="paper management bibliography bibtex reading list",
    install_requires=[
        'PyYAML>=5.3.1',
        'bibtexparser>=1.2.0',
        'file-magic>=0.4.0'
        ],
    extras_require={
        'widgets'  : [
            'jupyter>=1.0.0'
            ],
        'fulltext' : [
            'Whoosh-2.7.4',
            'pypandoc>=1.5',
            'pdftotext>=2.1.5',
            'textract>=1.6.3'
            ]
        },
    tests_require=['pytest'],
    entry_points = {
        'console_scripts': [
            'paperapp=paperapp.papercli:cli',
            ],
        },
    zip_safe=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Development Status :: 4 - Beta",
        "Framework :: Jupyter",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering"
    ],
    python_requires='>=3.6',
)
