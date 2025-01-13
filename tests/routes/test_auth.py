import unittest
from unittest.mock import patch

import pytest
from flask import session, url_for

from app.routes.auth import get_token
from run import app


class TestAuthBlueprint(unittest.TestCase):

    def setUp(self):
        """
        Set up the test class
        """
        app.config['SECRET'] = "Testing Secret"
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_get_token(self):
        """
        Test that the get_token function returns a valid access token from the database
        """
        token = get_token('123')
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertNotEqual(token, '')

    def test_user_logged_in(self):
        """
        Test that the user is redirected to the configuration page if they are already logged in
        """
        with self.client:
            # Simulate user already logged in
            with self.client.session_transaction() as sess:
                sess['user'] = {'id': '123',
                                'name': 'Test User',
                                'access_token': 'test_access_token',
                                'refresh_token': 'test_refresh_token',
                                'expires_in': 3600}

            # Call the authorization route
            response = self.client.get('/authorization')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/configure')

            # Assert that the user is redirected to the home page with a warning flash
            configure_response = self.client.get('/configure')
            self.assertEqual(configure_response.status_code, 200)
            self.assertIn('You are already logged in.', configure_response.data.decode())

    def test_user_not_logged_in(self):
        response = self.client.get('/authorization')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/callback', response.location)

    @pytest.mark.tryfirst()
    @patch('app.routes.mal_client.get_access_token')
    @patch('app.routes.mal_client.get_user_details')
    @patch('app.db.db.store_user')
    def test_callback(self, mock_store_user, mock_get_user_details, mock_get_access_token):
        """
        Test that the user is logged in and redirected to configuration page with a success message
        """
        # Mock the access token and user details
        mock_get_access_token.return_value = {'access_token': 'test_access_token',
                                              'refresh_token': 'test_refresh_token',
                                              'expires_in': 3600}
        mock_get_user_details.return_value = {'id': '123', 'name': 'Test User'}
        mock_store_user.return_value = None

        # Simulate the callback with a successful authorization code
        with self.client.session_transaction() as sess:
            sess['code_verifier'] = 'mocked_verifier'
        response = self.client.get('/callback?code=mocked_auth_code')

        # Assert that the user is redirected to the home page with a success message
        self.assertEqual(response.status_code, 302)

        response = self.client.get(response.location)
        self.assertIn('You are now logged in.', response.data.decode())

        # Check that the user was stored in the session
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['user']['id'], '123')
            self.assertEqual(sess['user']['name'], 'Test User')
            self.assertEqual(sess['user']['access_token'], 'test_access_token')
            self.assertEqual(sess['user']['refresh_token'], 'test_refresh_token')
            self.assertEqual(sess['user']['expires_in'], 3600)

    @patch('app.routes.mal_client.refresh_token')
    @patch('app.db.db.store_user')
    def test_refresh_token(self, mock_store_user, mock_refresh_token):
        """
        Test that the user's session is refreshed and the user is redirected to the configuration page
        """
        # Mock the refresh token response
        mock_refresh_token.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        }
        mock_store_user.return_value = None

        # Simulate a logged-in user session
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user'] = {'id': '123',
                                'name': 'Test User',
                                'access_token': 'old_access_token',
                                'refresh_token': 'old_refresh_token',
                                'expires_in': 3600}

            # Simulate the refresh endpoint
            redirect_response = self.client.get('/refresh')
            self.assertEqual(redirect_response.status_code, 302)

            # Manually manage the session after redirect
            with self.client.session_transaction() as sess:
                self.assertIn('user', sess)

                response = self.client.get(redirect_response.location)
                self.assertIn('MyAnimeList session refreshed.', response.data.decode())
                self.assertEqual(sess['user']['access_token'], 'new_access_token')
                self.assertEqual(sess['user']['refresh_token'], 'new_refresh_token')

    def test_session_expired(self):
        """
        Test that the user is logged out and redirected to the index page with a warning message
        """
        with self.client:
            with self.client.session_transaction() as sess:
                response = self.client.get('/refresh')
                response = self.client.get(response.location)
                self.assertIn('Session expired! Please log in to MyAnimeList again.', response.data.decode())
                self.assertIsNone(sess.get('user'))

    def test_logout_not_logged_in(self):
        """
        Test that the user is redirected to the index page with a warning message
        """
        redirect_response = self.client.get('/logout')
        self.assertEqual(redirect_response.status_code, 302)

        response = self.client.get(redirect_response.location)
        self.assertIn('You are not logged in.', response.data.decode())

    @pytest.mark.trylast()
    def test_logout(self):
        """
        Test that the user is logged out and redirected to the index page
        """
        with self.client:
            with self.client.session_transaction() as sess:
                sess['user'] = {'id': '123', 'name': 'Test User'}
                self.assertIn('user', sess)

                response = self.client.get('/logout')
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, url_for('index'))
                self.assertNotIn('user', session)
