#!/usr/bin/env python
# intj.com is the site where INTJs do everything
# like they would do it on Twitter, but not quite

import logging
import time
import re
from py2neo import neo4j, node, rel
import tornado.ioloop
from tornado.options import define, options
from tornado.httputil import url_concat
import tornado.web
import bcrypt
import json

logging.basicConfig(level = logging.INFO)

logger = logging.getLogger(__name__)

define('port',
       default = 8888,
       help = 'Run on the given port',
       type = int)

settings = { 'debug': True,
             'cookie_secret': 'bolv0.8er6bu' }

server_settings = { 'xheaders' : True }

salt = '$2a$12$5.OLqPRaoAhItdfAgNZZYe'

# Patches (will need to put it in a separate file)
# Maybe I'll need this, we'll see
# import py2neo
from py2neo.packages.httpstream.jsonstream \
    import (AwaitingData, UnexpectedCharacter, Tokeniser, EndOfStream)
# _Entity = py2neo.neo4j._Entity
# entity_patch_ftype = type(_Entity.get_properties)

def _read_digit(self):
    pos = self.data.tell()
    try:
        digit = self._read()
        if digit not in "0123456789eE-":
            self.data.seek(pos)
            raise UnexpectedCharacter(digit)
    except AwaitingData:
        self.data.seek(pos)
        raise AwaitingData()
    return digit

def _read_number(self):
    pos = self.data.tell()
    src = []
    has_fractional_part = False
    try:
        # check for sign
        ch = self._peek()
        if ch == '-':
            src.append(self._read())
        # read integer part
        ch = self._read_digit()
        src.append(ch)
        if ch != '0':
            while True:
                try:
                    src.append(self._read_digit())
                except (UnexpectedCharacter, EndOfStream):
                    break
        try:
            ch = self._peek()
        except EndOfStream:
            pass
        # read fractional part
        if ch == '.':
            has_fractional_part = True
            src.append(self._read())
            while True:
                try:
                    src.append(self._read_digit())
                except (UnexpectedCharacter, EndOfStream):
                    break
    except AwaitingData:
        # number potentially incomplete: need to wait for
        # further data or end of stream
        self.data.seek(pos)
        raise AwaitingData()
    src = "".join(src)
    if has_fractional_part:
        return src, float(src)
    else:
        return src, int(src)

# def entity_get_properties(self):
#     if not self.is_abstract:
#         size = 1024
#         response = self._properties_resource._get()._response
#         body = []
#         while True:
#             chunk = response.read(size)
#             if chunk:
#                 body.append(chunk)
#             else:
#                 break
            
#         logging.info('resources: %s' % body)
#         self._properties = json.loads(''.join(body))
#     return self._properties

# _Entity.get_properties = entity_get_properties
Tokeniser._read_digit = _read_digit
Tokeniser._read_number = _read_number

class IntjCrud():

    def __init__(self):
        self.db = neo4j.GraphDatabaseService()

    def create_user(self, user):
        self.db.create(node(name = user['name'],
                            password = user['password'],
                            registered = time.time()))
    
    def sanitize(self, dangerous):
        return '\\"'.join([re.sub(r'\\', r'\\\\', x)
                           for x in dangerous.split('"')])
        
    def get_user_by_password(self, password):
        query = neo4j.CypherQuery(
            self.db,
            """
            CYPHER 1.9
            START user = node(*)
            WHERE user.password? = {password}
            RETURN user
            """)
        try:
            return query.execute(password = self.sanitize(password)).data[0][0]
        except IndexError:
            return None

    def get_user_by_id(self, user_id):
        return self.db.node(user_id)

    def post_message(self, user_id, message):
        self.db.create(node(text = message['text'],
                            posted = time.time()),
                       rel(0, 'posted_by', user_id))

    def follow(self, follower_id, followed_id):
        self.db.create(rel(follower_id, 'posted_by', followed_id))

    def unfollow(self, follower_id, followed_id):
        pass

    def get_feed(self, user_id):
        pass

    def get_global_feed(self):
        pass

class BaseHandler(tornado.web.RequestHandler):

    @property
    def crud(self):
        if not self._crud:
                self._crud = IntjCrud()
        return self._crud

    def resolve_url(self, url):
        return '../html/' + url

    def get_login_url(self):
        return '/login'

    def get_profile_url(self):
        return '/profile'

    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        return user_json and tornado.escape.json_decode(user_json)
    
    def report_error(self):
        self.redirect(url_concat(
            self.get_login_url(), { 'error': self.error_message }))

    def set_current_user(self, user):
        logging.info('Current user is %s' % user)
        if user:
            self.set_secure_cookie(
                'user', tornado.escape.json_encode(user))
        else:
            self.clear_cookie('user')

class LoginHandler(BaseHandler):

    def __init__(self, application, request, **kwargs):
        super(LoginHandler, self).__init__(
            application, request, **kwargs)
        self.error_message = ''
        self._crud = None

    def get(self):
        self.render(self.resolve_url('login.html'),
                    next = self.get_argument('next', '/'),
                    message = self.get_argument('error', ''))

    def register(self, username, password):
        logging.info('Registering new user %s with password %s' % (username, password))
        try:
            self.crud.create_user({ 'name': username, 'password': password })
            return True
        except Exception as e:
            logging.error('Registration failed for user %s with password %s, reason: %s' %
                          (username, password, e))
            return False

    def post(self):
        username, password, password_confirmation = tuple(
            self.get_argument(x, '').encode('utf-8')
            for x in ('username', 'password', 'password_confiramtion'))

        user = None
        password_encrypted = None
        can_login = False
        
        if password:
            password_encrypted = bcrypt.hashpw(username + password, salt)
            user = self.crud.get_user_by_password(password_encrypted)
        else:
            self.error_message = 'Lacking password'

        if not username:
            self.error_message = 'Lacking name'

        if not self.error_message:
            logging.info('Found user %s for name %s' % (user, username))
            can_login = user and user['password'] and \
                        password_encrypted == user['password']

        if not can_login:
            if not self.error_message:
                self.error_message = 'Cannot login with these credentials'

        if ((not can_login) and password_confirmation and password and username):
            if password == password_confirmation:
                can_login = self.register(username, password_encrypted)
            else:
                self.error_message = 'Passwords don\'t match'
        
        if can_login:
            self.set_current_user(password_encrypted)
            self.redirect(self.get_profile_url())
        else:
            self.report_error()

class ProfileHandler(BaseHandler):
    
    def get(self):
        self.render(self.resolve_url('profile.html'),
                    next = self.get_argument('next', '/'),
                    message = self.get_argument('error', ''))

class SocialNetwork():

    def __init__(self):
        tornado.options.parse_command_line()
        logging.info('Starting Tornado web server on http://localhost:%s' % options.port)
        self.application = tornado.web.Application([
            (r'/login', LoginHandler),
            (r'/profile', ProfileHandler),
        ], **settings)
        self.application.listen(options.port, **server_settings)
        tornado.ioloop.IOLoop.instance().start()
