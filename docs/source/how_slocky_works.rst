Baisc
=====

This is designed to (hopefully) offer secure transmission of messages between
clients and a server. This is using the SSL/TLS library from the python standard
library however this is only as secure as TLS and the system SSL/TLS library (probably
openssl).

Slocky is designed to be simple way to get messages between a client and server. This works
by creating a self-signed certificate the first time you start the server and distributing
this to clients which connect. The client and server will pair together creating a trust of
the certificate. Messages can then be sent between the server and client with reasonable
expectation of security.

Pairing
-------

Pairing is how clients establish trust of the server. When an unpaired client connects, the
server will generate a passphrase which is hashed with the certificate and sent to the client.
The passphrase is also given to the person who enters it into the client. The client then
checks that the certificate it's recieved plus the passphrase produce the same hash allowing
it to verify that the certificate really did come from the server.

Once the client has been paired it shouldn't need to repair again however if the certificate
it has recieved has expired before the client has recieved the new certificate re-pairing must
occur. If for whatever reason the certificate changes when the client doesn't expect it to then
the client will re-pair with the server.

.. note:: Passphrases are a small set of simple US English words however if you're developing
   for an enviroment which has another language you can supply your own wordlist.

.. todo:: Maybe include a flow chart or psudocode explanation of the steps involved in pairing?

Messaging
---------

Slocky uses JSON as the message format between the client and server so any message can be
sent provided it is JSON serializable.
