from access_point import AccessPoint
from ssd1306 import SSD1306
from webserver import Response, WebServer
from wifi import WiFi

# Clients join this access point, then open http://192.168.4.1
# Leave AP_PASSWORD as None for an open network. A password must be at least 8 characters.
AP_SSID = "Pico Setup"
AP_PASSWORD = None

screen = SSD1306(sda=4, scl=5, width=128, height=64)
wifi = WiFi()
ap = AccessPoint()
server = WebServer()


def _escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _notice(message):
    if not message:
        return ""
    return "".join("<p>{}</p>".format(_escape(line)) for line in str(message).split("\n"))


def render(message=""):
    options = []
    for net in wifi.scan():
        options.append(
            '<label><input type="radio" name="ssid" value="{value}"> {name} ({security}, {rssi})</label>'.format(
                value=_escape(net.ssid),
                name=_escape(net.ssid),
                security=_escape(net.security),
                rssi=net.rssi,
            )
        )
    if not options:
        options.append("<p>No networks found.</p>")
    return """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wi-Fi</title>
<style>
body {{ font-family: sans-serif; margin: 1rem; }}
label {{ display: block; margin: 0.6rem 0; }}
input[type=password] {{ width: 100%; padding: 0.5rem; box-sizing: border-box; }}
button {{ padding: 0.6rem 1rem; }}
</style>
</head>
<body>
<h1>Wi-Fi</h1>
{notice}
<form method="post" action="/connect">
{options}
<p><input name="password" type="password" placeholder="Password"></p>
<p><button type="submit">Connect</button></p>
</form>
<p><a href="/">Scan again</a></p>
</body>
</html>
""".format(notice=_notice(message), options="\n".join(options))


def index(_request):
    return render()


def connect(request):
    ssid = request.form.get("ssid", "").strip()
    password = request.form.get("password") or None
    if not ssid:
        return render("Choose a network")
    screen.text("connecting")
    try:
        wifi.connect(ssid, password)
    except OSError as err:
        screen.text(str(err))
        return render(str(err))
    status = wifi.status()
    screen.text(status)
    return render(status)


def other(request):
    if request.method == "GET":
        return index(request)
    return Response("Not found", status=404, content_type="text/plain")


ap.start(AP_SSID, AP_PASSWORD)
print(ap.status())
screen.text(ap.status())

server.route("/", index)
server.route("/connect", connect, method="POST")
server.fallback(other)
print("open http://" + ap.status().split("\n")[1])
server.serve()
