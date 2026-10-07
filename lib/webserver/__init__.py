import socket


_REASONS = {
    200: "OK",
    302: "Found",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    500: "Internal Server Error",
}


class Request:
    def __init__(self, method, path, query, form, body):
        self.method = method
        self.path = path
        self.query = query
        self.form = form
        self.body = body


class Response:
    def __init__(self, body="", status=200, content_type="text/html", headers=None):
        self.body = body
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}


class WebServer:
    def __init__(self, port=80):
        self.port = port
        self._routes = {}
        self._fallback = None
        self._sock = None

    def route(self, path, handler, method="GET"):
        self._routes[(method.upper(), path)] = handler

    def fallback(self, handler):
        self._fallback = handler

    def serve(self):
        info = socket.getaddrinfo("0.0.0.0", self.port)[0][-1]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(info)
        sock.listen(1)
        self._sock = sock
        while True:
            try:
                conn, _addr = sock.accept()
            except OSError:
                break
            try:
                self._handle(conn)
            finally:
                conn.close()

    def close(self):
        sock = self._sock
        self._sock = None
        if sock is not None:
            sock.close()

    def _handle(self, conn):
        try:
            request = _read_request(conn)
        except OSError:
            return
        if request is None:
            return
        try:
            result = self._dispatch(request)
        except Exception as err:
            result = Response(str(err), status=500, content_type="text/plain")
        if isinstance(result, str):
            result = Response(result)
        _send(conn, result)

    def _dispatch(self, request):
        handler = self._routes.get((request.method, request.path))
        if handler is None:
            allowed = [method for method, path in self._routes if path == request.path]
            if allowed:
                return Response("Method not allowed", status=405, content_type="text/plain")
            if self._fallback is not None:
                return self._fallback(request)
            return Response("Not found", status=404, content_type="text/plain")
        return handler(request)


def _read_request(conn):
    conn.settimeout(8)
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(512)
        if not chunk:
            break
        data += chunk
        if len(data) > 4096:
            break
    if b"\r\n\r\n" not in data:
        return None
    head, rest = data.split(b"\r\n\r\n", 1)
    lines = head.split(b"\r\n")
    parts = lines[0].split(b" ")
    if len(parts) < 2:
        return None
    method = parts[0].decode().upper()
    target = parts[1].decode()
    path, _, query_text = target.partition("?")
    if not path:
        path = "/"
    headers = {}
    for line in lines[1:]:
        if b":" not in line:
            continue
        name, value = line.split(b":", 1)
        headers[name.strip().lower()] = value.strip()
    length = int(headers.get(b"content-length", b"0") or b"0")
    if length > 2048:
        _send(conn, Response("Payload too large", status=413, content_type="text/plain"))
        return None
    while len(rest) < length:
        chunk = conn.recv(512)
        if not chunk:
            break
        rest += chunk
    body = rest[:length]
    form = {}
    content_type = headers.get(b"content-type", b"")
    if b"application/x-www-form-urlencoded" in content_type or (method == "POST" and body and not content_type):
        form = _pairs(body)
    return Request(method, path, _pairs(query_text.encode()), form, body)


def _pairs(raw):
    found = {}
    for pair in raw.split(b"&"):
        if not pair:
            continue
        if b"=" in pair:
            key, value = pair.split(b"=", 1)
        else:
            key, value = pair, b""
        found[_unquote(key)] = _unquote(value)
    return found


def _unquote(raw):
    raw = raw.replace(b"+", b" ")
    out = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] == 0x25 and index + 2 < len(raw):
            try:
                out.append(int(raw[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass
        out.append(raw[index])
        index += 1
    return out.decode()


def _send(conn, response):
    if isinstance(response.body, str):
        body = response.body.encode()
    else:
        body = response.body
    reason = _REASONS.get(response.status, "OK")
    head = "HTTP/1.0 {:d} {:s}\r\nContent-Type: {:s}\r\nContent-Length: {:d}\r\nConnection: close\r\n".format(
        response.status, reason, response.content_type, len(body)
    )
    for name, value in response.headers.items():
        head += "{:s}: {:s}\r\n".format(name, value)
    _sendall(conn, head.encode() + b"\r\n" + body)


def _sendall(conn, data):
    while data:
        sent = conn.send(data)
        if sent is None or sent <= 0:
            break
        data = data[sent:]
