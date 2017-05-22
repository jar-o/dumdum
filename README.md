[![dumdum](dumdum.png)](dumdum.png)

[![Codix](https://codix.io/gh/badge/jar-o/dumdum)](https://codix.io/gh/repo/jar-o/dumdum)

Create dummy HTTP servers without writing code.

This module allows you to easily create "dummy" servers from simple descriptive
text. Need a fake server for testing, or maybe the service you're trying to
test doesn't have a "stage" environment? That's what this is for.

## Installation

You can install the extension with ``pip`` like

```
pip install dumdum
```

## Usage

`dumdum` is both a command-line utility and a library. It takes a simple
_stanza_ format and generates a web server with endpoints from that. E.g. to do
"hello world" you could do

```
printf "
> GET
> /hello
< body world
.
" | dumdum
```

This will create a server listening on the default port (`8001`). You can test with

```
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
```

`Dumdum` is a WSGI compliant library, so you can easily serve it from your own code like

```
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
```

If you're using the CLI, you can change the port by using the `--port` parameter. You can also tell `dumdum` to read the stanzas from a file with `--file path/to/file`.

## Stanza reference

_Stanzas_ are written in a simple text-based format. The format is partitioned into _Request_ (`>`) and _Response_ (`<`) sections, and a stanza ends with a period (`.`). You can specify more than one stanza per file or input.

### Request

The _Request_ section designates what will be matched. It's prefixed by `>` and at a minimum requires an _HTTP verb_ and a _request path_. These may be followed by a series of `header` directives, which then may be followed by a series of `param` directives, i.e.,

```
> VERB          (required)
> /path         (required)
> header ...    (optional, one or more)
> param  ...    (optional, one or more)
.
```

The `header` directive is of the format

```
> header <line>
```

The _line_ must match the standard HTTP header format, e.g.

```
> header Content-Type: application/json
```

The `param` directive is of the format

```
> param <name> is|like <value|regex>
```

where _name_ specifies the parameter to check. You specify `is` for an exact match, or `like` to do more complex regular expression matching. For example

```
> param userid is 1234
```

will match `GET /path?userid=1234`, while

```
> param userid like //[a-z]+1234$//
```

will match `GET /path?userid=abc1234`. Note that the regex is contained within double slashes.

#### JSON

dumdum understands JSON requests. And because of this, you may have nested values you want to match. A `param` name may use dotted notation to specify this nesting. E.g. if you have the following JSON

```
{
    "user": {
        "roles": [
            { "role": "admin" },
            { "role": "novice" },
        ]
    }
}
```

you can match on

```
> param user.roles.role is admin
```

### Response

The _Response_ section designates what will be returned if the _Request_ section matches. It's prefixed by `<`. This section is entirely optional, by default dumdum will return a `200` response.


```
< status <number>
< header <line>
< body <data>
.
```

Use _status_ to return a specific HTTP response code.

The _header_ directive allows you to set custom response headers. These must conform to the standard HTTP header format.

The _body_ directive can be a single line or multiple lines, and can contain any valid utf-8. If you specify multiple lines, you must use the `<<<` enclosure, e.g.

```
< body <<<
{
    "status": "OK",
    "hm": "简体中文测试"
}
<<<
```

### Example

Let's take a full example. Stanzas are matched from top to bottom. This allows you to make specific matches and "fall through" to default responses.

```
### Failure
> POST
> /register/device
> header Content-Type: application/json
> param user.devices.deviceID is abc123
> param user.id like //failauth//
< status 403
< header Content-Type: application/json
< body {"status":"not ok","message":"User ID is wrong"}
.

### Success
> POST
> /register/device
> header Content-Type: application/json
> param user.devices.deviceID is abc123
> param user.id like //succeedauth//
< status 200
< header Content-Type: application/json
< body {"status":"ok","message":"Device registered"}
.

### Default
> POST
> /register/device
< status 400
< header Content-Type: application/json
< body {"response":"not ok"}
.
```

The above input will respond with `403` on the following JSON

```
{
    "user": {
        "id": "USRfailauth",
        "devices":[
            { "deviceID": "abc123" },
            { "deviceID": "xyz123" }
        ]
    }
}
```

The following will fail to match on the `403` stanza, but be matched by the second `200` stanza:

```
{
    "user": {
        "id": "USRsucceedauth",
        "devices":[
            { "deviceID": "abc123" },
            { "deviceID": "xyz123" }
        ]
    }
}
```

Any other request, gibberish or not, will result in a `400`.  

_Robot image [designed by Freepik](http://www.freepik.com)._
