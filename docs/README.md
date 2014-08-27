ZTPServer Documentation
========================

[ZTPServer official documentation](http://ztpserver.readthedocs.org/) is built and hosted at (http://ReadTheDocs.org/).

Contributing
------------

See CONTRIBUTING.md for information on maintaining documentation.

Building / Publishing Docs locally
----------------------------------

* `make` \(default make target is now `make html`\)
* Open file://_build/html/index.html in your browser to view.
* Publish by copying `docs/_build/html/*` to the `gh-pages` branch

Documenting REST APIs
---------------------

REST APIs are documented via the [httpdomain](https://pythonhosted.org/sphinxcontrib-httpdomain/) plugin for sphinx.

