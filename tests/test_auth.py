from unittest import mock
import transaction
from .base import BaseTest, WebTest
from nthuion.models.auth import Token, FacebookUser, Email, User


class AuthTest(BaseTest):
    def test_acquire_token(self):
        from nthuion.models.auth import User, Token
        self.assertEqual(0, self.session.query(Token).count())
        u = User(name='name')
        self.session.add(u)
        tvalue = u.acquire_token()
        self.assertEqual(1, self.session.query(Token).count())
        self.assertEqual(
            u,
            self.session.query(Token).filter(Token.value == tvalue).one().user
        )


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


def valid_user_response(*args, **kwargs):
    return FakeResponse(
        200, {
            'id': '34502913498532310',
            'name': '340gieoj3',
            'email': 'test@example.com'
        }
    )


def bad_request_response(*args, **kwargs):
    return FakeResponse(400, {'error': 'gg'})


class FacebookLoginTest(WebTest):
    def test_facebook_login(self):
        with mock.patch('requests.get', valid_user_response):
            res = self.app.post_json(
                '/api/login/facebook', {'token': 'exxe'}, status=200
            )
        email = self.session.query(Email).one()
        facebook_user = self.session.query(FacebookUser).one()
        user = self.session.query(User).one()
        token = self.session.query(Token).one()
        self.assertEqual(user, email.user)
        self.assertEqual(user, token.user)
        self.assertEqual(user, facebook_user.user)
        self.assertEqual('test@example.com', email.address)
        self.assertEqual(token.value, res.json['token'])
        self.assertEqual(
            'https://graph.facebook.com/34502913498532310/picture',
            user.as_dict()['avatar_url']
        )

    def test_facebook_bad_login(self):
        with mock.patch('requests.get', bad_request_response):
            res = self.app.post_json(
                '/api/login/facebook', {'token': 'exxe'}, status=401
            )
        self.assertEqual(
            'Login failed: token rejected by facebook',
            res.json['error']['message']
        )

    def test_facebook_same_email(self):
        """
        If 2 users are registered with the same facebook email,
        the later one does not own the email address automatically
        """
        self.test_facebook_login()

        def valid_user_response2(*args, **kwargs):
            return FakeResponse(
                200, {
                    'id': '23r23few',
                    'name': 'duplicate',
                    'email': 'test@example.com'
                }
            )

        with mock.patch('requests.get', valid_user_response2):
            self.app.post_json(
                '/api/login/facebook', {'token': 'exxe'}, status=200
            )

        self.assertEqual(2, self.session.query(User).count())

        self.assertEqual(
            2, self.session.query(Email).count()
        )


class LogoutTest(WebTest):
    def test_logout_revokes_token(self):
        user = User(name='gg')
        self.session.add(user)
        self.session.add(Token(user=user, value='234564232234'))
        self.assertEqual(1, self.session.query(Token).count())
        self.app.post_json(
            '/api/logout',
            headers={'Authorization': 'Token 234564232234'},
            status=200
        )
        self.assertEqual(0, self.session.query(Token).count())
