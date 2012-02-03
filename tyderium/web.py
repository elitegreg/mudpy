from .http import Server, Response
import re

class HTTPError(Exception):
    def __init__(self, code, status, **info):
        self.code = code
        self.status = status
        self.info = info

class Site(Server):
    default_encoding = 'utf-8'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.routes = []

    def route(self, expression, method='GET', template=None):
        def wrapper(fun):
            self.routes.append((method,
                self._compile(expression), template, fun))
            return fun
        return wrapper

    def _compile(self, expression):
        parts = [r'^']
        for idx, val in enumerate(re.split(r':(\w+)', expression)):
            if idx & 1:
                parts.append(r'(?P<{}>[^/]+)'.format(val))
            else:
                parts.append(re.escape(val))
        parts.append(r'(?:$|\?)')
        return re.compile(''.join(parts))

    def dispatch(self, req, resp):
        for meth, ex, tpl, fun in self.routes:
            if meth != req.method:
                continue
            m = ex.match(req.uri)
            if m:
                dct = m.groupdict()
                dct.update(req.query)
                if meth == 'POST':
                    dct.update(req.post)
                res = fun(resp, **dct)
                if tpl is not None and isinstance(res, dict):
                    return self.render(tpl, **res)
                else:
                    return res
        else:
            raise HTTPError(404, 'Not Found')

    def render(self, name, **kw):
        return self.template_factory(name).render(**kw)

    def response_factory(self, request):
        response = Response(request)
        try:
            result = self.dispatch(request, response)
        except HTTPError as e:
            response.status(e.code, e.status)
            response.set_header('Content-Type', 'text/html; encoding={}'
                    .format(self.default_encoding))
            response.send_body(self.render('error',
                code=e.code, status=e.status, **e.info))
        else:
            if not response._status:
                response.status(200, 'OK')
            if not 'Content-Type' in response.headers:
                response.add_header('Content-Type', 'text/html; encoding={}'
                    .format(self.default_encoding))
            if isinstance(result, str):
                result = result.encode(self.default_encoding)
            response.send_body(result)
