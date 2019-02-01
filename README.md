# Cypherpath LTI App Example Project

This is an example application that can interface into a Learning Management System (LMS) like Moodle and SDI OS via the RESTful API.

# Getting Started

## System requirements

    * Linux
    * PostgreSQL
    * Python 2.7
    * Virtualenv

This application is based on Django 1.7; for information and documentation on the Django framework, see https://www.djangoproject.com/.

This application has only been tested on Linux, but should work on other POSIX systems, and may work on Windows as well. The only LMS that has been tested with this LTI application is Moodle.

## Installation

First, clone this project:

`git clone https://github.com/cypherpath/lti-app`

### Postgresql

Database settings are configured in `sdios_lti/settings.py`.  The default user is `sdios_lti` with password `sdios_lti`, using the database `sdios_lti`, connecting to PostgreSQL via a Unix domain socket.

Django supports more databases than just PostgreSQL, but this application has not been tested with any of them.

Most Django settings are the defaults; see https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/ for information on properly setting up the configuration.

To create the database and user, log into your Postgres server via the `psql` CLI as database administrator.  How to do this is system-dependent, so please consult your system documentation.

Once logged in, run the following:

```
CREATE DATABASE sdios_lti;
CREATE USER sdios_lti WITH PASSWORD 'sdios_lti';
GRANT ALL PRIVILEGES ON DATABASE sdios_lti TO sdios_lti;
```

Postgres is now ready for use.

### Python 2 virtual environment

It is highly recommended that a Python virtual environment be used.  To create a virtual environment for this application, run the following from the top-level directory (i.e. the directory containing the manage.py file):

`virtualenv --no-site-packages root`

Note: Ensure that the virtualenv you run is for **Python 2**, not Python 3.  The script may be called `virtualenv2` on your system.  

To activate the virtual environment inside the current shell:

`source root/bin/activate`

This assumes a Bourne-compatible shell.  If you are unfamiliar with Python virtual environments, please see https://virtualenv.pypa.io/en/latest/.

### Python 2 dependencies

Dependencies can now be installed.  Some dependencies require external libraries to be installed.  Pycrypto requires `libgmp`, and Psycopg2 requires PostgreSQL.  Note that on many systems separate development packages must be installed, such as `postgresql-server-dev` and `libgmp-dev`.  Consult your system's documentation for more information.  To install dependencies, run:

`pip install -r requirements.txt`

### Final steps
Now that the environment is configured, the database must be initialized.  This is done using the `migrate` command:

`./manage.py migrate`

Now a superuser must be created:

`./managed.py createsuperuser`

At this point, the system is ready to run.  Django's internal web server can be spun up as follows:

`./manage.py runserver 0:80`

This will run a webserver listening on port 80 on all addresses.  Log in with the superuser account that was created in the previous step.


### In Production

This is only an example LTI application to use with an LMS and SDI OS. You are free to use this in production at your own risk. If using this in production, please make sure to change the default database username/password, and Django `SECRET_KEY` in `sdios_lti/settings.py`. Also remember to set `DEBUG=false` as well.

#### Dedicated webserver

A dedicated webserver can also be used to run this application and is highly recommended, presuming it supports the WSGI specification.  For information on running Django applications with the Nginx webserver, see http://uwsgi.readthedocs.org/en/latest/Nginx.html.

Nginx requires uwsgi to be installed: this can be accomplished by running:

`pip install uwsgi`

## Usage

Before configuration and use of this LTI app, make sure you have an SDI OS API application created. The creation of an SDI OS API application is out of the scope of this README so consult the SDI OS API documentation.

The following are descriptions of the four sections on the LTI app's homepage.

![lti-app-screenshot-home](https://user-images.githubusercontent.com/23587713/52088964-2cca7800-2562-11e9-8a87-7ebb8a041dd1.png)

### SDIs

The SDIs page shows all SDIs in the API user's account will appear. To make an SDI available for the LMS, it will need to be Exported. 

![lti-app-screenshot-sdi-export](https://user-images.githubusercontent.com/23587713/52089098-8763d400-2562-11e9-9ec7-19503dec0a94.png)

The LTI Key needs to be passed to the custom parameters within the LTI plugin as the following example string:

`sdi=57ceb389-a87e-4321-be64-0c8a95dbbcb3` 

![lti-app-screenshot-sdis](https://user-images.githubusercontent.com/23587713/52088871-effe8100-2561-11e9-91ca-7d35c2fe4edc.png)

### Consumers

The Consumers page is where the LMS consumer credentials are created. The credentials from this page will be used in the LMS to authenticate this LTI app.

![lti-app-screenshot-consumers](https://user-images.githubusercontent.com/23587713/52088906-03115100-2562-11e9-946a-445cce0f2086.png)

### Users

The Users page shows the users that are currently using under each consumer key created from the Consumers page. Clicking on the consumer key row will display the LTI User ID and the SDI OS Username for each LMS user.


![lti-app-screenshot-users](https://user-images.githubusercontent.com/23587713/52088939-191f1180-2562-11e9-9644-5e1290d143b4.png)

### Settings

The Settings page is used to input the SDI OS domain URL, the API username, password, client ID, and client secret.

![lti-app-screenshot-settings](https://user-images.githubusercontent.com/23587713/52088955-23d9a680-2562-11e9-98e4-0cd63eb49b83.png)
