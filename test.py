#!/usr/bin/env python

import unittest
from intj import SocialNetwork
import requests
import multiprocessing
import tornado
import logging
import time

logging.basicConfig(level = logging.INFO)

logger = logging.getLogger(__name__)

class worker(multiprocessing.Process):

    def run(self):
        SocialNetwork()

    def stop(self, timeout = 5):
        tornado.ioloop.IOLoop.instance().stop()
        time.sleep(timeout)
        self.terminate()

class CollectorTestCase(unittest.TestCase):

    _worker = None
    
    def setUp(self):
        self._worker = worker()
        self._worker.start()
        logger.info('setUp finished')

    def tearDown(self):
        self._worker.stop()

    def test_register_user(self):
        # Seems like this won't save cookies, so the test
        # can never succeed, will need to think of something else...
        # Maybe Selenium?
        requests.get(r'http://localhost/login')
        requests.post(r'http://localhost/login',
                      data = { 'username': 'test',
                               'passowrd': 'test-password',
                               'password_confirmation': 'test-pasword' })

    def test_login(self):
        pass

    def test_post_article(self):
        pass

    def test_retrieve_article(self):
        pass

    def test_follow(self):
        pass

    def test_unfollow(self):
        pass

    def test_retrieve_feed(self):
        pass

if __name__ == '__main__':
    unittest.main()
