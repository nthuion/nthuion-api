from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .meta import Base


class User(Base):

    id = Column(Integer, primary_key=True)


class FacebookUser(Base):

    id = Column(String(40), primary_key=True)
    # facebook says an id is a "numeric string"
    # https://developers.facebook.com/docs/graph-api/reference/v2.7/user

    email = Column(String(254), nullable=False)
    # see also http://isemail.info/about

    access_token = Column(Text)

    user_id = Column(Integer, ForeignKey(User.id), unique=True, index=True)
    user = relationship(User, uselist=False)
