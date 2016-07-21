from zope.interface import implementer
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated, Everyone
from pyramid.httpexceptions import HTTPBadRequest
from .models import User, Token


@implementer(IAuthenticationPolicy)
class TokenAuthenticationPolicy:

    def forget(self, request):
        value = self.unauthenticated_userid(request)
        if value is not None:
            request.db.query(Token.value == value).delete()

    def remember(self, request, userid, **kw):
        pass
        # the login functions do it well

    def authenticated_userid(self, request):
        value = self.unauthenticated_userid(request)
        return request.db.query(User)\
            .filter(Token.value == value)\
            .filter(Token.user_id == User.id)\
            .get()  # None on not found

    def unauthenticated_userid(self, request):
        authorization = request.headers.get('Authorization')
        if authorization is not None:
            try:
                type_, value = authorization.split(maxsplit=1)
                if type_ != 'Token':
                    raise HTTPBadRequest(
                        'Unknown Authorization type {}'.format(type_)
                    )
                else:
                    return value
            except ValueError:
                raise HTTPBadRequest('Invalid Authorization header format')
        else:
            return None

    def effective_principals(self, request):
        user = self.authenticated_userid(request)
        if user is None:
            return [Everyone]
        else:
            return [user, Everyone, Authenticated]