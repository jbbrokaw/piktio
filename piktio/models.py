from sqlalchemy import (
    Column,
    Integer,
    Table,
    Unicode,
    ForeignKey,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy.orm import (
    relationship,
    backref,
)

from apex.models import (AuthID, DBSession)

# DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

follower_followee = Table(
    "follower_followee",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("piktio_profile.id"), primary_key=True),
    Column("followee_id", Integer, ForeignKey("piktio_profile.id"), primary_key=True)
)


class PiktioProfile(Base):
    __tablename__ = 'piktio_profile'

    id = Column(Integer, primary_key=True)
    auth_id = Column(Integer, ForeignKey(AuthID.id), index=True, nullable=False)

    followers = relationship("PiktioProfile",
                             secondary=follower_followee,
                             primaryjoin=(id == follower_followee.c.followee_id),
                             secondaryjoin=(id == follower_followee.c.follower_id),
                             backref="followees")

    display_name = Column(Unicode(80))

    user = relationship(AuthID, backref=backref('profile', uselist=False))


class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    subject = Column(Unicode(72))


class Predicate(Base):
    __tablename__ = 'predicate'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    predicate = Column(Unicode(72))


class Description(Base):
    __tablename__ = 'description'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    description = Column(Unicode(144))


class Drawing(Base):
    __tablename__ = 'drawing'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    identifier = Column(Unicode(80), nullable=True)


game_authors = Table(
    'game_authors',
    Base.metadata,
    Column('game_id', Integer, ForeignKey('game.id')),
    Column('author_id', Integer, ForeignKey('piktio_profile.id'))
)


class Game(Base):
    __tablename__ = "game"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey(Subject.id))
    predicate_id = Column(Integer, ForeignKey(Predicate.id), nullable=True)
    first_drawing_id = Column(Integer, ForeignKey(Drawing.id), nullable=True)
    first_description_id = Column(Integer, ForeignKey(Description.id), nullable=True)
    second_drawing_id = Column(Integer, ForeignKey(Drawing.id), nullable=True)
    second_description_id = Column(Integer, ForeignKey(Description.id), nullable=True)

    subject = relationship(Subject, backref="games")
    predicate = relationship(Predicate, backref="games")
    first_drawing = relationship(Drawing, backref="games_first",
                                 foreign_keys=[first_drawing_id])
    first_description = relationship(Description, backref="games_first",
                                     foreign_keys=[first_description_id])
    second_drawing = relationship(Drawing, backref="games_second",
                                  foreign_keys=[second_drawing_id])
    second_description = relationship(Description, backref="games_second",
                                      foreign_keys=[second_description_id])

    authors = relationship(PiktioProfile, secondary=game_authors, backref="games")


class Rating(Base):
    __tablename__ = "rating"
    game = Column(Integer, ForeignKey(Game.id), primary_key=True)
    rater = Column(Integer, ForeignKey(PiktioProfile.id), primary_key=True)
    rating = Column(Integer)
