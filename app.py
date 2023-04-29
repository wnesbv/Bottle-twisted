
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource

from autobahn.twisted.resource import WebSocketResource, WSGIRootResource

from bottle import (
    request,
    template,
    Bottle,
)

from chat.urls import chat, ServerFactory, ServerProtocol

from auth.urls import auth
from blog.urls import blog
from user.urls import user

from imp_exp_csv.urls import filecsv

from composite.parts import parts


app = Bottle()

app.mount("/auth", auth)
app.mount("/blog", blog)
app.mount("/chat", chat)
app.mount("/user", user)
app.mount("/csv", filecsv)

app.mount("/static", parts)


users = set()


@app.route("/")
def index():
    return template("index.html")


@app.route("/messages")
def messages():
    msg = request.query["msg"]
    return template("messages.html", msg=msg)


if __name__ == "__main__":

    wsFactory = ServerFactory("ws://127.0.0.1:8080")
    wsFactory.protocol = ServerProtocol
    wsResource = WebSocketResource(wsFactory)
    wsgiResource = WSGIResource(reactor, reactor.getThreadPool(), app)
    rootResource = WSGIRootResource(wsgiResource, {b"websocket": wsResource})
    site = Site(rootResource)
    reactor.listenTCP(8080, site)
    reactor.run()
