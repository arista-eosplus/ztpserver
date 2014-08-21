Contributing to ZTP Server Docs
===============================

Documenting REST APIs
---------------------

REST APIs are documented via the [httpdomain](https://pythonhosted.org/sphinxcontrib-httpdomain/) plugin for sphinx.

Docstrings in the code
----------------------

Other documentation extracted from the code should be in the [Google](http://google-styleguide.googlecode.com/svn/trunk/pyguide.html#Comments) format readable by the [Napoleon](http://sphinxcontrib-napoleon.readthedocs.org/en/latest/) module.

Editing RST documents
---------------------

Documentation is maintained in .rst files in the docs/ directory and in Google-style, or spinxcontrib-httpdomain docstrings within the code.   Images and diagrams may be included in the _static/ directory.  Please be sure you have built and viewed your work prior to sumbitting a pull-request back to the ‘develop’ branch.


Building and testing documentation generation
---------------------------------------------

To test contributions to the documentation, ensure you have the prerequisites, below, then follow the build and test instructions before submitting a pull request.

prerequisites
``````````````

    sudo pip install sphinx_rtd_theme
    sudo pip install sphinxcontrib-napoleon

    # httpdomain (for REST APIs)
        sudo pip install sphinxcontrib-httpdomain
        **OR**
        hg clone https://bitbucket.org/birkenfeld/sphinx-contrib
        cd sphinx-contrib/httpdomain/
        sudo python setup.py install

    # If you wish to test building epub or PDF documents, you will need latex.
    # latexpdf may require the following
        https://tug.org/mactex/   OR
        texlive-latex-recommended
        texlive-latex-extra
        texlive-fonts-recommended

    sudo tlmgr option repository   ftp://ftp.tug.org/historic/systems/texlive/2013/tlnet-final
    sudo tlmgr --force install titlesec
    sudo tlmgr install framed
    sudo tlmgr install threeparttable
    sudo tlmgr install wrapfig
    sudo tlmgr install multirow
    sudo tlmgr install collection-fontsrecommended

Building / Publishing Docs locally
``````````````````````````````````

* `make` \(default make target is now `make html`\)
* Open file://_build/html/index.html in your browser to view.
* Publish by copying `docs/_build/html/*` to the `gh-pages` branch

