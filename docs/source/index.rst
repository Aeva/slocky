
Slocky
======

Slocky is a client-server simple communication framework which is built on top
of TLS. A single central server is required, server and client are then able
to pass any JSON serializable object as a message between each other.

Slocky will automate creating the SSL/TLS certificate the first time the server
is started. The first time the client and server connect you will need to pair
them together.

Contents
--------

.. toctree::
   :maxdepth: 1

   how_slocky_works
