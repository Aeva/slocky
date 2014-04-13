
========
 Client
========

Getting the basic client into your program shouldn't be too difficult, you should also
take a look at the examples provided with slocky in addition to this documentation. If
you have not already read the documentation on :doc:`../how_slocky_works` you should do so
before continuing with this documentation.

You will probably want to override some of the `slocky.client.SlockyClient` methods. The methods
you probably wish to override are:

.. automodule:: slocky.client
.. autoclass:: SlockyClient
   :members: on_message, on_connected, on_checksum_fail, on_validate

.. warning:: You must store the certificate you get in a secure location, anyone/anything
	     that has access to the certificate is able to alter it and cause your client
	     to trust anything it wants.


Once you've defined you're cleint you'll want to instanciate it and connect to the server.
This will do the pairing if it's nessesery. Once the client has connected to the server
you will be able to use the client:

  >>> client = MySlockyClient("my.slocky.server.tld", 8000, "/path/to/client/directory")
  >>> client.connect()

To send messages you can use the `SlockyClient.send` method:

  >>> client.send("Hello!")
  >>> client.send({"slocky": "Awesome"})

That's all there really is to it.
