import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.options
import json
import time
import config
from group_sender import GroupManager
import logging
from handlers import QueryHandler, NotifyHandler
from validators import Validator
import tornado.gen
import traceback


class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    @tornado.web.asynchronous
    @tornado.gen.engine
    def open(self, *args, **kwargs):
        redis = self.application.query_handler.get_redis()
        user_id = self.get_argument("user_id")
        group_name = self.get_argument("group_name")
        user_token = self.get_argument("token")
        if user_id and group_name and user_token:
            key = "WEBSOCKET_TOKEN_%s" % str(user_id)
            valid_token = yield tornado.gen.Task(redis.get, key)
            if str(valid_token) == str(user_token):
                self.application.manager.register(self)
            else:
                self.write_message(json.dumps({"error": "token invalid"}))
                self.close()
        else:
            self.write_message(json.dumps({"error": "not enough parameters"}))
            self.close()

    @tornado.web.asynchronous
    @tornado.gen.engine
    def on_message(self, msg):
        try:
            data = json.loads(msg)
        except:
            data = None
            self.write_message(json.dumps({"detail":"invalid json"}))

        valid_result = self.application.validator.validate(data)

        if valid_result is True:
            if data["message_type"] == "query":
                handler = self.application.query_handler
                if data["message"] == "user_amount":
                    try:
                        user_id = data["args"]["user_id"]
                        message = yield self.application.query_handler.get_user_amount(user_id)
                    except KeyError:
                        message = {"detail": "empty user_id"}

                elif data["message"] == "current_ticker":
                    redis = handler.get_redis()
                    coinpair = data["args"]["coinpair"].replace("/", "_")
                    key = "PRICE_%s" % coinpair
                    price = yield tornado.gen.Task(redis.hget, key, "price")
                    message = {"price": price}

                else:
                    message = None

            elif data["message_type"] == "notification":
                user_type = self.application.query_handler.get_user_type(self.get_argument("user_id"))
                if user_type == 3:
                    message = None
                else:
                    try:
                        message = {"title": data["args"]["title"], "content": data["args"]["content"]}
                    except KeyError:
                        message = {"detail": "empty title or content"}
                handler = self.application.notify_handler
            else:
                message = None
                handler = None

            if data["send_type"] == "private" and message and handler:
                try:
                    send_user_id = data["args"]["send_user_id"]
                    send_group_name = data["args"]["send_group_name"]

                except KeyError:
                    self.write_message(json.dumps({"detail": "empty send_user_id or send_group_name"}))

                try:
                    user = self.application.manager.get_user(send_user_id, send_group_name)
                    handler.private_message(user, message)
                except:
                    self.write_message(json.dumps({"detail": "send_user or send_group not exist"}))

            elif data["send_type"] == "group" and message and handler:
                try:
                    send_group_name = data["args"]["send_group_name"]
                except KeyError:
                    self.write_message(json.dumps({"detail": "empty group_name"}))

                try:
                    user = self.application.manager.get_group_user(send_group_name)
                    handler.broadcast(user, message)
                except:
                    self.write_message(json.dumps({"detail": "send_group not exist"}))
            elif data["send_type"] == "all" and message and handler:
                user = self.application.manager.get_all_user()
                handler.broadcast(user, message)

        else:
            self.write_message(json.dumps(valid_result))

    def on_close(self):
        self.application.manager.unregister(self)


class Application(tornado.web.Application):
    def __init__(self):
        self.manager = GroupManager()
        self.query_handler = QueryHandler()
        self.notify_handler = NotifyHandler()
        self.validator = Validator()

        handlers = [
            (r'/', IndexPageHandler),
            (r'/ws', WebSocketHandler)
        ]
        settings = { "template_path": "."}
        settings["log_function"] = config.log_func
        tornado.web.Application.__init__(self, handlers=handlers, **settings)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    ws_app = Application()
    server = tornado.httpserver.HTTPServer(ws_app)
    server.listen(8080)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()