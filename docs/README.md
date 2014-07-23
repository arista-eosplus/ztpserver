ZTP Server Documentation
========================

Requirements
------------

The following packages must be installed to build the documentation::

    sudo pip install sphinx_rtd_theme
    sudo pip install sphinxcontrib-napoleon
    # httpdomain (for REST APIs)
        hg clone https://bitbucket.org/birkenfeld/sphinx-contrib
        cd sphinx-contrib/httpdomain/
        sudo python setup.py install

Building / Publishing Docs
--------------------------

* `make` \(default make target is now `make html`\)
* Open file://_build/html/index.html in your browser to view.
* Publish by copying `docs/_build/html/*` to the `gh-pages` branch

Documenting REST APIs
---------------------

REST APIs are documented via the [httpdomain](https://pythonhosted.org/sphinxcontrib-httpdomain/) plugin for sphinx.

