============
dumdum
============
Create fake HTTP servers with simple stanzas.

This module allows you to easily create "dummy" servers from simple descriptive
text. Need a dummy server for testing, or maybe the service you're trying to
test doesn't have a "stage" environment? That's what this is for.


Installation
===============
You can install the extension with ``pip`` like

::
    pip install dumdum

Usage
===============
``dumdum`` is both a command-line utility and a library. It takes a simple
_stanza_ format and generates a web server with endpoints from that. E.g. to do
"hello world" you could do

::

    printf "
    > GET
    > /hello
    < body world
    .
    " | dumdum

Then you can test with

::

    % curl http://localhost:8001/hello

    > GET /hello HTTP/1.1
    > Host: localhost:8001
    > User-Agent: curl/7.51.0
    > Accept: */*
    >
    * HTTP 1.0, assume close after body
    < HTTP/1.0 200 OK
    < Date: Wed, 17 May 2017 18:43:39 GMT
    < Server: WSGIServer/0.1 Python/2.7.13
    < Content-type: text/plain
    < Content-Length: 7

    world

This will create a server listening on the default port (``8001``). ``Dumdum`` is a
WSGI compliant library, so you can easily serve it from your own code like

::

    from wsgiref.simple_server import make_server
    from dumdum import Dumdum

    dum = Dumdum("""
    > GET
    > /hello
    < body world
    .
    """)
    srv = make_server('', 5000, dum.server)
    srv.serve_forever()

Source and further details can be found at https://github.com/jar-o/dumdum
