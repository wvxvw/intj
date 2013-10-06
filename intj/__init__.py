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
# import json

from patches import patch
patch()

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

class IntjCrud():

    def __init__(self):
        self.db = neo4j.GraphDatabaseService()

    def create_user(self, user):
        self.db.create(node(name = user['name'],
                            password = user['password'],
                            registered = time.time()))
    
    def get_user_by_password(self, password):
        query = neo4j.CypherQuery(
            self.db,
            """
            CYPHER 1.9
            START user = node(*)
            WHERE has(user.password) and user.password = {password}
            RETURN user
            """)
        try:
            return query.execute(password = password).data[0][0]
        except IndexError:
            return None

    def get_user_by_id(self, user_id):
        return self.db.node(user_id)

    def post_message(self, user_id, message):
        logging.info('Saving message by %s\n%s' % (user_id, message))
        self.db.create(node(text = message, posted = time.time()),
                       rel(0, 'posted_by', self.db.node(user_id)))

    def get_feed(self, user_id, limit = 10):
        query = neo4j.CypherQuery(
            self.db,
            """
            CYPHER 1.9
            START author = node({id})
            MATCH (article)-[?:posted_by]->(author)
            RETURN article
            LIMIT {max_articles}
            """)
        feeds = query.execute(id = user_id, max_articles = limit).data
        logging.info('Found feeds %s' % feeds)
        return { 'feeds':[{ 'text' : x.article['text'],
                            'posted': x.article['posted'],
                            'url': '/article/%d' % x.article._id }
                          for x in feeds] }

    def get_all_feeds(self, limit = 10):
        # If I knew how to substitute `*' for id, I could merge this
        # into `get_feed'
        query = neo4j.CypherQuery(
            self.db,
            """
            CYPHER 1.9
            START author = node(*)
            MATCH (article)-[:posted_by]->(author)
            RETURN article, author
            LIMIT {max_articles}
            """)
        feeds = query.execute(max_articles = limit).data
        logging.info('Found feeds %s' % feeds)
        return { 'feeds':[{ 'text' : x.article['text'],
                            'posted': x.article['posted'],
                            'url': '/article/%d' % x.article._id,
                            'author_id': x.author._id,
                            'author_name': x.author['name'] }
                          for x in feeds] }

    def get_article(self, article_id):
        return self.db.node(article_id)['text']

    def get_user_profile(self, user_id):
        logging.info('Fetching profile for user: %s' % user_id)
        # Must be a bug in Cypher, there should be no need to
        # use `DISTINCT' in this query, users can only follow
        # other users once.
        query = neo4j.CypherQuery(
            self.db,
            """
            CYPHER 1.9
            START user = node({id})
            MATCH
            (user)-[?:follows]->(_followed),
            (_follower)-[?:follows]->(user)
            RETURN user,
            COLLECT(DISTINCT _followed) as followed,
            COLLECT(DISTINCT _follower) as follower
            """)
        data = query.execute(id = user_id).data
        
        # Because using the original JSON would be too simple...
        followed, followers = [], []
        def node_to_user(node):
            return { 'name': node['name'],
                     'registered': node['registered'],
                     'id': node._id }
        for row in data:
            followed += map(node_to_user, row.followed)
            followers += map(node_to_user, row.follower)
        return { 'user': node_to_user(data[0].user),
                 'followed': followed,
                 'followers': followers }

    def follow(self, follower_id, followed_id):
        self.db.create(rel(self.db.node(follower_id),
                           'follows', self.db.node(followed_id)))

    def unfollow(self, follower_id, followed_id):
        query = neo4j.CypherQuery(
            self.db,
            """
            CYPHER 1.9
            START
            followed = node({followed_id}),
            follower = node({follower_id}),
            MATCH (follower)-[r?:follows]->(followed)
            DELETE r
            RETURN null
            """)
        query.execute(follower_id = follower_id, followed_id = followed_id)

class BaseHandler(tornado.web.RequestHandler):

    @property
    def crud(self):
        if not self._crud: self._crud = IntjCrud()
        return self._crud

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(
            application, request, **kwargs)
        self.error_message = ''
        self._crud = None

    def resolve_url(self, url):
        return '../html/' + url

    def resolve_and_render(self, url):
        self.render(self.resolve_url(url))

    def get_login_url(self):
        return '/login'

    def get_network_url(self):
        return '/social-network'

    def get_article_url(self):
        return '/article'

    def get_profile_url(self):
        return '/profile'

    def get_current_user(self):
        user_json = self.get_secure_cookie('user')
        logging.info('Current user: %s' % user_json)
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

    def get_current_user_id(self):
        return self.crud.get_user_by_password(self.get_current_user())._id

    def ensure_current_user_id(self, maybe_id):
        if not maybe_id or maybe_id == 'me':
            return self.get_current_user_id()
        else:
            return int(maybe_id)

class LoginHandler(BaseHandler):

    def get(self):
        self.resolve_and_render('login.html')

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
            self.redirect(self.get_network_url())
        else:
            self.report_error()

class SocialNetworkHandler(BaseHandler):
    
    def get(self):
        self.resolve_and_render('social-network.html')

class FeedHandler(BaseHandler):
    
    def post(self, user_id):
        if not user_id or user_id == 'all':
            self.write(self.crud.get_all_feeds())
        else:
            self.write(self.crud.get_feed(
                self.ensure_current_user_id(user_id)))

class ProfileHandler(BaseHandler):

    def get(self, user_id):
        self.resolve_and_render('profile.html')
    
    def post(self, user_id):
        self.write(self.crud.get_user_profile(
            self.ensure_current_user_id(user_id)))

class PostHandler(BaseHandler):
    
    def post(self):
        # Need to promote maximum article length to some sort of
        # settings
        article = self.request.body
        article = re.sub(r'<', r'&lt;',
                         re.sub(r'>', r'&gt;',
                                article[:min(1024, len(article))]))
        # This can be reduced to a single query
        user = self.crud.get_user_by_password(self.get_current_user())
        self.crud.post_message(user._id, article)

class ArticleHandler(BaseHandler):

    def get(self, article_id):
        self.resolve_and_render('article.html')
    
    def post(self, article_id):
        self.write(self.crud.get_article(article_id))

class FollowHandler(BaseHandler):
    
    def post(self, follower_id):
        self.crud.follow(int(follower_id), self.get_current_user_id())

class UnfollowHandler(BaseHandler):
    
    def post(self, follower_id):
        self.crud.unfollow(int(follower_id), self.get_current_user_id())

class SocialNetwork(object):

    def __init__(self):
        tornado.options.parse_command_line()
        logging.info('Starting Tornado web server on http://localhost:%s' % options.port)
        self.application = tornado.web.Application([
            (r'/login', LoginHandler),
            (r'/social-network', SocialNetworkHandler),
            (r'/post', PostHandler),
            (r'/profile/([^\/]+)', ProfileHandler),
            (r'/feed/([^\/]+)', FeedHandler),
            (r'/article/([^\/]+)', ArticleHandler),
            (r'/follow/([^\/]+)', FollowHandler),
            (r'/unfollow/([^\/]+)', UnfollowHandler),
        ], **settings)
        self.application.listen(options.port, **server_settings)
        tornado.ioloop.IOLoop.instance().start()
