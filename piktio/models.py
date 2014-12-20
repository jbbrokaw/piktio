from sqlalchemy import (
    Column,
    Integer,
    Table,
    Unicode,
    ForeignKey,
)
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    relationship,
    backref
)

from apex.models import (AuthID, DBSession)

# DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

_STEPS = ['subject', 'predicate', 'first_drawing',
          'first_description', 'second_drawing',
          'second_description']


def copy_game_to_step(game, step):
    """Make a copy of a game object, but only up to the step
    (integer from 1 to 6)"""
    new_game = Game()
    for i in xrange(step):
        attr_name = _STEPS[i] + "_id"
        attached_object = game.__getattribute__(_STEPS[i])
        new_game.__setattr__(attr_name, attached_object.id)
        author = DBSession.query(PiktioProfile)\
            .filter(PiktioProfile.id == attached_object.author_id).one()
        new_game.authors.append(author)
    return new_game

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

    display_name = Column(Unicode(72), unique=True)

    user = relationship(AuthID, backref=backref('profile', uselist=False))


class Subject(Base):
    __tablename__ = 'subject'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    subject = Column(Unicode(72))

    author = relationship(PiktioProfile, backref='subjects')


class Predicate(Base):
    __tablename__ = 'predicate'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    predicate = Column(Unicode(72))

    author = relationship(PiktioProfile, backref='predicates')


class Description(Base):
    __tablename__ = 'description'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    description = Column(Unicode(144))

    author = relationship(PiktioProfile, backref='descriptions')


class Drawing(Base):
    __tablename__ = 'drawing'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    identifier = Column(Unicode(80), unique=True)

    author = relationship(PiktioProfile, backref='drawings')

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
    time_completed = Column(DateTime, nullable=True)

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
