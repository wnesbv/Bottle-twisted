import json, jwt

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

from bottle import (
    Bottle,
    template,
    request,
)

from composite.parts import con, f_dt, visited, who_is_who


JWT_ALGORITHM = "HS256"
SECRET_KEY = "!0_77!%_#)p3gk-m_np8sukvi1^9_^38s^l-g505fsqg-1j&2&"

chat = Bottle()


def save_msg(story, user):
    i_user = jwt.decode(user, SECRET_KEY, JWT_ALGORITHM)
    i_id = i_user["id"]

    data = (story, f_dt, i_id)
    cur = con.cursor()
    sql = "INSERT INTO chat_table (story, generated, user_list)VALUES (?,?,?)"
    cur.execute(sql, data)
    con.commit()
    cur.close()
    return data


def save_img(upload, user):
    i_user = jwt.decode(user, SECRET_KEY, JWT_ALGORITHM)
    i_id = i_user["id"]
    img = f"/static/chat/{upload}"

    data = (img, f_dt, i_id)
    cur = con.cursor()
    sql = "INSERT INTO chat_table (upload, generated, user_list)VALUES (?,?,?)"
    cur.execute(sql, data)
    con.commit()
    cur.close()
    return data


# ..
class ServerProtocol(WebSocketServerProtocol):
    def onConnect(self, request):
        user_cookie = request.headers["cookie"]
        original = user_cookie
        removed = original.replace("visited=", "")
        item_user = jwt.decode(removed, SECRET_KEY, JWT_ALGORITHM)
        in_user = item_user["mail"]

        print("onConnect..! {}".format(in_user))

        return (None, {"i": in_user})

    def onOpen(self):
        self.factory.register(self)
        print("onOpen..!")

    def onMessage(self, payload, isBinary):
        self.factory.broadcast(payload, isBinary)
        print("onMessage..!")

    def onClose(self, wasClean, code, reason):
        self.factory.unregister(self)
        print("onClose..!")


class ServerFactory(WebSocketServerFactory):
    protocol = ServerProtocol

    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []

    def register(self, client):
        if client not in self.clients:
            self.clients.append(client)
            print("register client.. {}".format(client.peer))

    def unregister(self, client):
        if client in self.clients:
            self.clients.remove(client)
            print("unregistered client.. {}".format(client.peer))

    def broadcast(self, payload, isBinary):
        i_save = []

        for i in self.clients:
            i.sendMessage(payload, isBinary)
            i_save.append(payload)

        data = json.loads(payload)
        if data.get("fle"):
            i_save = save_img(data["fle"], data["user"])
        if data.get("msg"):
            i_save = save_msg(data["msg"], data["user"])

        print("broadcasted message to {} clients".format(len(self.clients)))


# ..


@chat.route("/")
@visited()
def chat_all_get():
    token = request.get_cookie("visited")
    for_user = who_is_who()[0]
    # ..
    cur = con.cursor()
    cur.execute("SELECT * FROM chat_table")
    res = cur.fetchall()
    cur.close()

    return template(
        "chat/chat.html",
        res=res,
        token=token,
        for_user=for_user,
    )
