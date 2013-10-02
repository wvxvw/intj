#!/usr/bin/env python

import tornado.ioloop
from tornado.options import define, options # , logging
import tornado.web
import bcrypt
import logging

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

define('port',
       default = 8888,
       help = 'Run on the given port',
       type = int)

settings = { 'debug': True }

server_settings = { 'xheaders' : True }

class BaseHandler(tornado.web.RequestHandler):
    def get_login_url(self):
        return '/login'

    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        return user_json and tornado.escape.json_decode(user_json)

class LoginHandler(BaseHandler):
    
    def __init__(self, application, request, **kwargs):
        super(LoginHandler, self).__init__(
            application, request, **kwargs)
        self.error_message = ''

    def resolve_url(self, url):
        return 'html/' + url

    def get(self):
        self.render(self.resolve_url('login.html'),
                    next = self.get_argument('next', '/'),
                    message = self.get_argument('error', ''))

    def register(self, username, password):
        already_taken = False # self.application.syncdb['users'].find_one(
            # { 'user': username })
        if already_taken:
            self.error_message = 'Login name already taken'
        else:
            user = { 'name': username }
            user['password'] = password
        return already_taken

    def report_error(self):
        self.redirect(self.resolve_url('login') + self.error_message)

    def post(self):
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        password_confirmation = self.get_argument(
            'password_confirmation', '')
        user = { 'name': username }# self.application.syncdb['users'].find_one(
            # { 'name': username })
        password_encrypted = bcrypt.hashpw(password, user['password'])
        can_login = user and user['password'] and password_encrypted == user['password']

        if not can_login:
            self.error_message = 'Cannot login with these credentials'
        
        if (not can_login and username and password and password_confirmation):
            if password == password_confirmation:
                can_login = self.register(username, password_encrypted)
            else:
                self.error_message = 'Passwords do not match'
        if can_login:
            self.set_current_user(username)
            self.redirect(self.resolve_url('profile'))
        else:
            self.report_error()

    def set_current_user(self, user):
        logging.info('Current user is %s' + user)
        if user:
            self.set_secure_cookie(
                'user', tornado.escape.json_encode(user))
        else:
            self.clear_cookie('user')

def main():
    tornado.options.parse_command_line()
    logging.info('Starting Tornado web server on http://localhost:%s' % options.port)
    application = tornado.web.Application([
        (r'/login', LoginHandler),
    ], cookie_secret = 'bolv0.8er6bu', **settings)
    application.listen(options.port, **server_settings)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
