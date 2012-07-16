SignInApp
=========

A sign in application designed to interface to the Roster project.

Requirements
------------
Python 3
PyQt4
A server running the Roster django application

Configuration
-------------
Edit settings.py and set the BASE\_URL and LOGIN\_USERNAME appropriately.
Due to security concerns, we recommend NOT setting the LOGIN\_PASSWORD and
using a dedicated user for LOGIN\_USERNAME.
The other settings shouldn't need tweaking unless you have a very customized
Roster application setup.
