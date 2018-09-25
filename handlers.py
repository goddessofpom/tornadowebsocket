from group_sender import SenderMixin
import tornadoredis
import config
from asyncio import events
import tormysql
import json
import tornado.gen
from tornado.gen import coroutine
import tornado.web
from tormysql import DictCursor
import traceback


class QueryHandler(SenderMixin):
    def __init__(self):
        CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=config.redis_config["max_connections"],
                                                      wait_for_available=True)
        self.redis = tornadoredis.Client(host=config.redis_config["host"], port=config.redis_config["port"],
                                         connection_pool=CONNECTION_POOL, selected_db=config.redis_config["db"])

        self.mysql = tormysql.ConnectionPool(
                         max_connections = config.mysql_config["max_connections"], #max open connections
                         idle_seconds = config.mysql_config["idle_seconds"], #conntion idle timeout time, 0 is not timeout
                         wait_connection_timeout = config.mysql_config["wait_connection_timeout"], #wait connection timeout
                         host = config.mysql_config["host"],
                         port = config.mysql_config["port"],
                         user = config.mysql_config["user"],
                         passwd = config.mysql_config["passwd"],
                         db = config.mysql_config["db"],
                         charset = config.mysql_config["charset"]
                    )

    def get_redis(self):
        return self.redis

    def get_mysql(self):
        return self.mysql


    @coroutine
    def get_user_type(self, user_id):
        with (yield self.mysql.Connection()) as conn:
            with conn.cursor() as cursor:
                yield  cursor.execute("SELECT user_type FROM user WHERE id = %s" % user_id)
                datas = cursor.fetchone()
                yield  conn.commit()
        return datas


    @coroutine
    def get_user_amount(self, user_id):
        with (yield self.mysql.Connection()) as conn:
            with conn.cursor(cursor_cls=DictCursor) as cursor:
                yield cursor.execute("SELECT amount FROM user WHERE id = %s" % user_id)
                datas = cursor.fetchone()
                yield conn.commit()

        # yield self.mysql.close()
        return datas


class NotifyHandler(SenderMixin):
    pass
