# import sys
# import werkzeug.contrib.sessions
# import sys
# import os

# from odoo import http, tools
# from odoo.tools.func import lazy_property

# if sys.version_info > (3,):
#     import _pickle as cPickle
#     unicode = str
# else:
#     import cPickle

# SESSION_TIMEOUT = 60 * 60 * 24 * 7  # 1 weeks in seconds


# def is_redis_session_store_activated():
#     return tools.config.get('enable_redis')


# try:
#     import redis
# except ImportError:
#     if is_redis_session_store_activated():
#         raise ImportError(
#             'Please install package python3-redis: '
#             'apt install python3-redis')


# class RedisSessionStore(werkzeug.contrib.sessions.SessionStore):

#     def __init__(self, *args, **kwargs):
#         super(RedisSessionStore, self).__init__(*args, **kwargs)
#         self.expire = kwargs.get('expire', SESSION_TIMEOUT)
#         self.key_prefix = kwargs.get('key_prefix', '')
#         self.redis = redis.Redis(
#             host=tools.config.get('redis_host', 'localhost'),
#             port=int(tools.config.get('redis_port', 6379)),
#             db=int(tools.config.get('redis_dbindex', 1)),
#             password=tools.config.get('redis_pass', None))
#         self._is_redis_server_running()

#     def save(self, session):
#         key = self._get_session_key(session.sid)
#         data = cPickle.dumps(dict(session))
#         self.redis.setex(name=key, value=data, time=self.expire)

#     def delete(self, session):
#         key = self._get_session_key(session.sid)
#         self.redis.delete(key)

#     def _get_session_key(self, sid):
#         key = self.key_prefix + sid
#         if isinstance(key, unicode):
#             key = key.encode('utf-8')
#         return key

#     def get(self, sid):
#         key = self._get_session_key(sid)
#         data = self.redis.get(key)
#         if data:
#             self.redis.setex(name=key, value=data, time=self.expire)
#             data = cPickle.loads(data)
#         else:
#             data = {}
#         return self.session_class(data, sid, False)

#     def _is_redis_server_running(self):
#         try:
#             self.redis.ping()
#         except redis.ConnectionError:
#             raise redis.ConnectionError('Redis server is not responding')


# if is_redis_session_store_activated():

#     # Patch methods of openerp.http to use Redis instead of filesystem

#     def session_gc(session_store):
#         # Override to ignore file unlink
#         # because sessions are not stored in files
#         pass

#     @lazy_property
#     def session_store(self):
#         # Override to use Redis instead of filestystem
#         return RedisSessionStore(session_class=http.OpenERPSession)

#     http.session_gc = session_gc
#     http.Root.session_store = session_store

from odoo.tools.func import lazy_property
from odoo import http, tools
import sys
import os
import werkzeug.contrib.sessions
import redis
import pickle
import logging

log = logging.getLogger(__name__)

SESSION_TIMEOUT = 60 * 60 * 24 * 7  # TODO: make this configurable!


def get_config(name, default):
    return os.environ.get(name.upper(),
                          tools.config.get(name, default))


class RedisSessionStore(werkzeug.contrib.sessions.SessionStore):

    def __init__(self, *args, **kwargs):
        super(RedisSessionStore, self).__init__(*args, **kwargs)
        self.expire = kwargs.get('expire', SESSION_TIMEOUT)
        self.key_prefix = kwargs.get('key_prefix', '')
        self.redis = redis.Redis(
            host=get_config('redis_host', 'localhost'),
            port=int(get_config('redis_port', 6379)),
            db=int(get_config('redis_dbindex', 1)),
            password=get_config('redis_pass', None))
        self._is_redis_server_running()

    def save(self, session):
        key = self._get_session_key(session.sid)
        data = pickle.dumps(dict(session))
        self.redis.setex(name=key, value=data, time=self.expire)

    def delete(self, session):
        key = self._get_session_key(session.sid)
        self.redis.delete(key)

    def _get_session_key(self, sid):
        key = self.key_prefix + sid
        if isinstance(key, str):
            key = key.encode('utf-8')
        return key

    def get(self, sid):
        key = self._get_session_key(sid)
        data = self.redis.get(key)
        if data:
            self.redis.setex(name=key, value=data, time=self.expire)
            data = pickle.loads(data)
        else:
            data = {}
        return self.session_class(data, sid, False)

    def _is_redis_server_running(self):
        try:
            self.redis.ping()
        except redis.ConnectionError:
            raise redis.ConnectionError('Redis server is not responding')


def setup():

    # Patch methods of openerp.http to use Redis instead of filesystem
    log.info("Using Redis session store. Host: " +
             str(get_config('redis_host', 'localhost')))

    def session_gc(session_store):
        # Override to ignore file unlink
        # because sessions are not stored in files
        pass

    @lazy_property
    def session_store(self):
        # Override to use Redis instead of filestystem
        return RedisSessionStore(session_class=http.OpenERPSession)

    http.session_gc = session_gc
    http.Root.session_store = session_store