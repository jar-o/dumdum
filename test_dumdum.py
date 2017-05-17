import unittest

from dumdum import Dumdum, DumdumParser
from wsgiref.simple_server import make_server, WSGIServer

stanzas = """
> GET
> /hello
< status 418
< body world
.
"""
class TestDumdum(unittest.TestCase):
    def test_all(self):
        dum = Dumdum(stanzas)
        assert isinstance(dum, Dumdum)
        assert dum.user_stanzas == stanzas
        assert '/hello' in dum.Stanzas['GET']
        srv = make_server('', 9999, dum.server)
        assert isinstance(srv, WSGIServer)

if __name__ == '__main__':
    unittest.main()

