import multiprocessing
from setuptools import setup, find_packages
setup(
    name = "tableauNetworkLayout",
    version = "0.01",
    packages = find_packages(),

    # Dependencies on other packages:
    # Couldn't get numpy install to work without
    # an out-of-band: sudo apt-get install python-dev
    setup_requires   = ['nose>=1.1.2'],
    install_requires = ['networkx>=2.0',
                        'numpy>=1.13.3',
                        'configparser>=3.3.0r2', 
                        'argparse>=1.2.1', 
                        ],
    tests_require    = ['sentinels>=0.0.6', 'nose>=1.0'],

    # Unit tests; they are initiated via 'python setup.py test'
    #test_suite       = 'json_to_relation/test',
    test_suite       = 'nose.collector', 

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
     #   '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
     #   'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author = "Andreas Paepcke",
    #author_email = "me@example.com",
    description = "Lays out nodes of a small network for visualization in Tableau.",
    license = "BSD",
    keywords = "network, nodes, layout",
    url = "git@github.com/tableauNetworkLayout",   # project home page, if any
)
