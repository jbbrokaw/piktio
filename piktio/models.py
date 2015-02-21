from sqlalchemy import (
    Column,
    Integer,
    Table,
    Unicode,
    ForeignKey,
    Float
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


def get_valid_game(request):
    """Get a valid game for the step in request.session['step']
    'Valid' means the game is complete to the previous step, has not been
    worked on by request.user, and the prompt/drawing has not been previously
    rejected by request.user"""
    if request.session['step'] == 'predicate':
        next_game = DBSession.query(Game)\
            .filter(
                ~Game.subject_id.is_(None),
                Game.predicate_id.is_(None),
                ~Game.authors.contains(request.user),
            ).first()
        return next_game

    if request.session['step'] == 'first_drawing':
        subject_strikes = DBSession.query(Strikes)\
            .filter(
                Strikes.author_id == request.user.id,
                ~Strikes.subject_id.is_(None)
            ).all()

        predicate_strikes = DBSession.query(Strikes)\
            .filter(
                Strikes.author_id == request.user.id,
                ~Strikes.predicate_id.is_(None)
            ).all()

        bad_subject_ids = [strike.subject_id for strike in subject_strikes]
        bad_predicate_ids = [strike.predicate_id for strike in predicate_strikes]

        next_game = DBSession.query(Game)\
            .filter(
                ~Game.predicate_id.is_(None),
                Game.first_drawing_id.is_(None),
                ~Game.authors.contains(request.user),
                ~Game.subject_id.in_(bad_subject_ids),
                ~Game.predicate_id.in_(bad_predicate_ids)
            ).first()

        return next_game

    if request.session['step'] == 'first_description':
        drawing_strikes = DBSession.query(Strikes)\
            .filter(
                Strikes.author_id == request.user.id,
                ~Strikes.drawing_id.is_(None)
            ).all()

        bad_drawing_ids = [strike.drawing_id for strike in drawing_strikes]

        next_game = DBSession.query(Game)\
            .filter(
                ~Game.first_drawing_id.is_(None),
                Game.first_description_id.is_(None),
                ~Game.authors.contains(request.user),
                ~Game.first_drawing_id.in_(bad_drawing_ids)
            ).first()

        return next_game

    if request.session['step'] == 'second_drawing':
        description_strikes = DBSession.query(Strikes)\
            .filter(
                Strikes.author_id == request.user.id,
                ~Strikes.description_id.is_(None)
            ).all()

        bad_description_ids = [strike.description_id for strike in description_strikes]

        next_game = DBSession.query(Game)\
            .filter(
                ~Game.first_description_id.is_(None),
                Game.second_drawing_id.is_(None),
                ~Game.authors.contains(request.user),
                ~Game.first_description_id.in_(bad_description_ids)
            ).first()

        return next_game

    if request.session['step'] == 'second_description':
        drawing_strikes = DBSession.query(Strikes)\
            .filter(
                Strikes.author_id == request.user.id,
                ~Strikes.drawing_id.is_(None)
            ).all()

        bad_drawing_ids = [strike.drawing_id for strike in drawing_strikes]

        next_game = DBSession.query(Game)\
            .filter(
                ~Game.second_drawing_id.is_(None),
                Game.second_description_id.is_(None),
                ~Game.authors.contains(request.user),
                ~Game.second_drawing_id.in_(bad_drawing_ids)
            ).first()

        return next_game


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


class InviteAddress(Base):
    __tablename__ = "invite_address"
    id = Column(Integer, primary_key=True)
    email = Column(Unicode(140), unique=True, nullable=False)


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
    Column('game_id', Integer, ForeignKey('game.id'), primary_key=True),
    Column('author_id', Integer, ForeignKey('piktio_profile.id'), primary_key=True)
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
    time_completed = Column(DateTime, nullable=True, index=True)
    score = Column(Float, default="1.0")

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


class Strikes(Base):
    __tablename__ = "strikes"
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey(PiktioProfile.id), index=True)
    subject_id = Column(Integer, ForeignKey(Subject.id), index=True, nullable=True)
    predicate_id = Column(Integer, ForeignKey(Predicate.id), index=True, nullable=True)
    drawing_id = Column(Integer, ForeignKey(Drawing.id), index=True, nullable=True)
    description_id = Column(Integer, ForeignKey(Description.id), index=True, nullable=True)

    author = relationship(PiktioProfile, backref='strikes')
    subject = relationship(Subject, backref='strikes')
    predicate = relationship(Predicate, backref='strikes')
    drawing = relationship(Drawing, backref='strikes')
    description = relationship(Description, backref='strikes')
