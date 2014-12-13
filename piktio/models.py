from sqlalchemy import (
    Column,
    Integer,
    Table,
    Unicode,
    ForeignKey,
    types,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref,
    )

from zope.sqlalchemy import ZopeTransactionExtension

from apex.models import (AuthID, AuthUser)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

follower_followee = Table("follower_followee", Base.metadata,
    Column("follower_id", Integer, ForeignKey("piktio_profile.id"), primary_key=True),
    Column("followee_id", Integer, ForeignKey("piktio_profile.id"), primary_key=True))


class PiktioProfile(Base):
    __tablename__ = 'piktio_profile'

    id = Column(Integer, primary_key=True)
    auth_id = Column(Integer, ForeignKey(AuthID.id), index=True, nullable=False)

    followers = relationship("PiktioProfile",
                        secondary=follower_followee,
                        primaryjoin=id==follower_followee.c.followee_id,
                        secondaryjoin=id==follower_followee.c.follower_id,
                        backref="followees")

    display_name = Column(Unicode(80))

    user = relationship(AuthID, backref=backref('profile', uselist=False))

class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    subject = Column(Unicode(150))

class Predicate(Base):
    __tablename__ = 'predicate'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    predicate = Column(Unicode(150))

class Description(Base):
    __tablename__ = 'description'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    description = Column(Unicode(300))

class Drawing(Base):
    __tablename__ = 'drawing'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    identifier = Column(Unicode(80), nullable=True)

class Game(Base):
    __tablename__ = "game"
    id = Column(Integer, primary_key=True)
    subject = Column(Integer, ForeignKey(Subject.id))
    predicate = Column(Integer, ForeignKey(Predicate.id), nullable=True)
    first_drawing = Column(Integer, ForeignKey(Drawing.id), nullable=True)
    first_description = Column(Integer, ForeignKey(Description.id), nullable=True)
    second_drawing = Column(Integer, ForeignKey(Drawing.id), nullable=True)
    second_description = Column(Integer, ForeignKey(Description.id), nullable=True)

class Rating(Base):
    __tablename__ = "rating"
    game = Column(Integer, ForeignKey(Game.id), primary_key=True)
    rater = Column(Integer, ForeignKey(PiktioProfile.id), primary_key=True)
    rating = Column(Integer)
