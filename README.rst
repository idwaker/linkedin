Linkedin Crawler
================

WIP
---


To install (Python 3)

::

    $ python -m venv venv
    $ ./venv/bin/pip install -r requirements.txt

Ubuntu

::

    $ sudo apt-get update && sudo apt-get upgrade
    $ sudo apt-get install build-essentials python-dev libssl-dev libffi-dev
    $ sudo apt-get install python-virtualenv
    $ virtualenv venv
    $ ./venv/bin/pip install pip --upgrade
    $ ./venv/bin/pip install -r requirements.txt
    $ ./venv/bin/pip install pyopenssl [ incase of insecure warning / or just to be safe ]

To store password in keychain

::

    $ python linkedin.py store me@email.com
    Password: **


To run crawler

::

    $ python linkedin.py crawl me@email.com list_of_names.csv dump_profiles_here.csv --browser=firefox
