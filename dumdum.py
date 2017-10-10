# -*- coding: utf-8 -*-
"""
A grammar to define "dummy" endpoints and behaviors based on parameters.
"""

import os, sys, json, re, time, logging
from urlparse import urlparse
from pyparsing import *
from cgi import parse_qs
import pprint

logger = logging.getLogger(__name__)

# Debug stuff
PP = pprint.PrettyPrinter(indent=2)
def dbg(o):
    if 'DUMDEBUG' in os.environ:
        print('DEBUG ---------------->')
        PP.pprint(o)
        print('---------------------->')


# Status codes
http_status_codes_map = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "Request-URI Too Long",
    415: "Unsupported Media Type",
    416: "Requested Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    444: "Connection Closed Without Response",
    451: "Unavailable For Legal Reasons",
    499: "Client Closed Request",
    500: "Internal Server Error",
    501: "Not Implemented",
    503: "Service Unavailable",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"
}
def status_map(code):
    return str(int(code)) + ' ' + http_status_codes_map[int(code)]


# Grammar hence
# Defines some common symbols
newline = '\n'
request_start = Keyword('>')
response_start = Keyword('<')
comment = OneOrMore(Word('#') + Word(printables + ' '))
unicodePrintables = u''.join(unichr(c) for c in xrange(sys.maxunicode)
                             if not unichr(c).isspace())

# Defines HTTP verbs
verb_get = Word('GET')
verb_post = Word('POST')
verb_put = Word('PUT')
verb_delete = Word('DELETE')
verb_head = Word('HEAD')
verb = verb_get | verb_post | verb_put | verb_delete | verb_head
verb_line = request_start + verb + Optional(Suppress(',')) + Optional(delimitedList(verb))

# Defines relative url path
xalphas = Word(alphanums + '$-_@.&+!*"\'(),%/')
rel_path = request_start + xalphas

# Defines parameters
param = Keyword('param') | Keyword('PARAM')
param_maybe = Keyword('param_maybe') | Keyword('PARAM_MAYBE')
kw_param_is = Keyword('is') | Keyword('IS')
kw_param_like = Keyword('like') | Keyword('LIKE')
param_name = xalphas
param_val = xalphas
param_re = QuotedString(quoteChar='//')
param_S = request_start + (param ^ param_maybe) + param_name + kw_param_is + param_val
param_R = request_start + (param ^ param_maybe) + param_name + kw_param_like + param_re
header = request_start + Keyword('header') + Word(printables + ' ')

# Defines response values
delay = response_start + Keyword('delay') + Word(nums) # NOTE milliseconds
header_resp = response_start + Keyword('header') + Word(printables + ' ')
status = response_start + Keyword('status') + Word(nums)

body_resp = response_start + Keyword('body') + \
    (Word(' ' + printables + unicodePrintables) ^ \
        QuotedString(quoteChar='<<<', escQuote='<<<<<<', multiline=True))
# This echos the request body, used as an alt to '< body ...' above
echo_resp = response_start + Keyword('echo')

# Defines the stanza list
stanza_end = LineStart() + '.' + LineEnd()

# The parser
class DumdumParser(object):
    class EchoFlag(object):
        pass
    def __init__(self, user_input):
        self.S = {}
        self.stanza = Group(
                verb_line.setParseAction(self.process_verbs) + \
                Optional(Suppress(comment))
            ) + \
            Group(
                rel_path.setParseAction(self.process_path) + \
                Optional(Suppress(comment))
            ) + \
            ZeroOrMore(
                Group(header.setParseAction(self.process_header)) + \
                Optional(Suppress(comment))
            ) + \
            ZeroOrMore(
                Group(
                    param_S.setParseAction(self.process_param) ^ \
                    param_R.setParseAction(self.process_param)
                ) + \
                Optional(Suppress(comment))
            ) + \
            ZeroOrMore(
                Group(
                    delay.setParseAction(self.process_resp_delay) + \
                    Optional(Suppress(comment))
                 )
            ) + \
            ZeroOrMore(
                Group(
                    status.setParseAction(self.process_resp_status) + \
                    Optional(Suppress(comment))
                )
            ) + \
            ZeroOrMore(
                Group(
                    header_resp.setParseAction(self.process_resp_header) + \
                    Optional(Suppress(comment))
                )
            ) + \
            ZeroOrMore(
                Group(
                    body_resp.setParseAction(self.process_resp_body) ^ \
                    echo_resp.setParseAction(self.process_resp_echo)
                ) + \
                Optional(Suppress(comment))
            ) + \
            Suppress(stanza_end.setParseAction(self.save_stanza))

        self.stanzas = OneOrMore(Group(
                    Optional(Suppress(comment)) + \
                    self.stanza + \
                    Optional(Suppress(comment))
                ))

        # This is a top-down parser, but we register handlers on specific
        # pattern matches, and using these "internal globals" allows us to keep
        # state straight.
        self.current_path = None
        self.current_verbs = []
        self.reqobj = None # stanza object from user input
        self.respobj = None # stanza object from user input
        dbg(user_input.decode('utf-8'))

        # Parse the user data
        self.stanzas.parseString(user_input.decode('utf-8'))

    def process_verbs(self, tokens): # The VERB line ALWAYS starts a request stanza
        self.reqobj = {}
        # Defaults
        self.respobj = {
            'status': status_map(200),
            'body':'',
        }
        self.current_verbs = tokens[1:]
        for verb in self.current_verbs:
            if verb not in self.S: self.S[verb] = {}

    def process_path(self, tokens):
        self.current_path = tokens[1]
        for verb in self.current_verbs:
            if self.current_path not in self.S[verb]:
                self.S[verb][self.current_path] = []

    def process_param(self, tokens):
        p = tokens[2:]
        if 'params' not in self.reqobj: self.reqobj['params'] = {}
        if p[1] == 'like':
            dbg("process_param() %s" % p)
            self.reqobj['params'][p[0]] = re.compile(p[2])
        else:
            self.reqobj['params'][p[0]] = p[2]

    def process_header(self, tokens):
        def header_cgi_key(header):
            h = header.upper().replace('-', '_')
            if h != 'CONTENT_TYPE':
                return 'HTTP_' + h # In CGI this precedes most headers
            else:
                return h
        h = tokens[2:][0].split(': ')
        if 'headers' not in self.reqobj: self.reqobj['headers'] = {}
        self.reqobj['headers'][header_cgi_key(h[0])] = h[1]

    def process_resp_status(self, tokens):
        self.respobj['status'] = status_map(tokens[2])

    def process_resp_delay(self, tokens):
        self.respobj['delay'] = tokens[2]

    def process_resp_header(self, tokens):
        h = tokens[2:][0].split(': ')
        if 'headers' not in self.respobj: self.respobj['headers'] = {}
        self.respobj['headers'][h[0]] = h[1]

    def process_resp_body(self, tokens):
        b = tokens[2:][0]
        self.respobj['body'] = b.strip() # TODO is this wise?

    def process_resp_echo(self, tokens):
        self.respobj['body'] = DumdumParser.EchoFlag()

    def save_stanza(self, tokens):
        if self.reqobj:
            for verb in self.current_verbs:
                if self.respobj: self.reqobj['response'] = self.respobj
                self.S[verb][self.current_path].append(self.reqobj)
        elif not self.reqobj and self.respobj:
            self.reqobj = { 'response': self.respobj }
            for verb in self.current_verbs:
                self.S[verb][self.current_path].append(self.reqobj)


# The server
class Dumdum(object):
    def __init__(self, user_stanzas):
        self.user_stanzas = user_stanzas
        self.parser = DumdumParser(user_stanzas)
        self.Stanzas = self.parser.S

    def server(self, env, start_response):
        # Helper functions hence
        def bad_req(msg="Sorry I couldn't help."):
            status = '400 Bad Request'  # HTTP Status
            headers = [('Content-type', 'text/plain')]  # HTTP Headers
            start_response(status, headers)
            return [msg]

        def flatten_json(y):
            delim='.'
            out = {}

            def flatten(x, name=''):
                if type(x) is dict:
                    for a in x:
                        flatten(x[a], name + a + delim)
                elif type(x) is list:
                    i = 0
                    for a in x:
                        flatten(a, name)
                        i += 1
                else:
                    nam = name[:-len(delim)]
                    if nam not in out:
                        out[nam] = [x]
                    else:
                        out[nam].append(x)

            flatten(y)
            return out


        # Handler hence
        # The environment variable CONTENT_LENGTH may be empty or missing
        try:
            request_body_size = int(env.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
        try:
            request_body = env['wsgi.input'].read(request_body_size)
        except Exception:
            pass

        verb = env['REQUEST_METHOD']
        url = urlparse(env['PATH_INFO'])

        logger.info(
            "\nCGI ENV: %s\n\n%s %s\n\n%s\n\n" %
            (PP.pformat(env), verb, url.path, request_body))

        if verb in self.Stanzas and url.path in self.Stanzas[verb]:
            for curr_Stz in self.Stanzas[verb][url.path]: # check every stanza under this path
                is_json = False
                match = True

                # compare headers
                if 'headers' in curr_Stz:
                    for h in curr_Stz['headers']:
                        sh = curr_Stz['headers']
                        if h in env and env[h] == sh[h]:
                            if h == 'CONTENT_TYPE' and sh[h].lower() == 'application/json':
                                is_json = True
                        else:
                            match = False
                            break

                # compare params
                if match:
                    sp = None
                    if 'params' in curr_Stz: sp = curr_Stz['params']
                    dbg('Stanza params=%s' % sp)
                    if is_json and request_body and sp:
                        try:
                            j_rb = json.loads(request_body)
                            fj_rb = flatten_json(j_rb)
                            dbg(json.dumps(fj_rb, indent=2,
                                           sort_keys=True))
                        except ValueError:
                            return bad_req("Error parsing: %s" % request_body)

                        for szparam in sp:
                            dbg('szparam=%s   match %s' % (szparam, match))
                            if match == False: break

                            if szparam not in fj_rb:
                                match = False
                                break
                            else:
                                # Check all provided values from input, and if
                                # one of them matches, then

                                matchone = False
                                for v in fj_rb[szparam]:
                                    dbg('v=%s   szparam=%s' % (v, sp[szparam]))
                                    if isinstance(sp[szparam], re._pattern_type):
                                        if sp[szparam].search(v):
                                            dbg('Match! regex')
                                            matchone = True
                                            break
                                    else:
                                        if v == sp[szparam]:
                                            dbg('Match! exact')
                                            matchone = True
                                            break
                                match = matchone
                    elif sp:
                            if 'QUERY_STRING' in env and env['QUERY_STRING'] != '':
                                qs = parse_qs(env['QUERY_STRING'])
                            elif 'wsgi.input' in env:
                                # TODO assumes urlencode form params...
                                qs = parse_qs(request_body)

                            print qs
                            print sp
                            for szparam in sp:
                                dbg('szparam=%s   match %s' % (szparam, match))
                                if match == False: break

                                if szparam not in qs:
                                    match = False
                                    break
                                else:
                                    matchone = False
                                    for v in qs[szparam]:
                                        dbg('v=%s   szparam=%s' % (v, sp[szparam]))
                                        if isinstance(sp[szparam], re._pattern_type):
                                            print '....?'
                                            print sp[szparam].search(v)
                                            if sp[szparam].search(v):
                                                dbg('Match! regex')
                                                matchone = True
                                                break
                                        else:
                                            if v == sp[szparam]:
                                                dbg('Match! exact')
                                                matchone = True
                                                break
                                    match = matchone


                    if match:
                        if 'response' in curr_Stz:
                            resp = curr_Stz['response']
                            if 'delay' in resp:
                                time.sleep(float(resp['delay'])/1000.0)
                            status = resp['status']
                            hdrs = []
                            if 'headers' in resp:
                                for h in resp['headers']:
                                    hdrs.append( (str(h),
                                                  str(resp['headers'][h])) )
                            start_response(status, hdrs)
                            if type(resp['body']) is DumdumParser.EchoFlag:
                                return request_body
                            else:
                                return [resp['body'].encode('utf-8')]
        # We matched nothing
        return bad_req()


if __name__ == "__main__":
    import argparse
    from wsgiref.simple_server import make_server

    def read_from_stdin():
        stz = ''
        for line in sys.stdin:
            stz += line
        return stz

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', help='set port for server (default 8001)')
    parser.add_argument('--file', help='file containing dumdum stanzas')
    parser.add_argument('--verbose', help='dump request and response info',
            action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.WARNING)


    if not args.file:
        user_stanza = read_from_stdin()
    else:
        with open(args.file, 'r') as f:
            user_stanza = f.read()

    dumdum = Dumdum(user_stanza)
    port = args.port or 8001
    srv = make_server('', int(port), dumdum.server)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nBye.')
