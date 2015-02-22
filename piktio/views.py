import uuid
import datetime
import json

from pyramid.view import view_config  # , forbidden_view_config
from pyramid.httpexceptions import HTTPFound
from apex.lib.flash import flash
from apex.lib.libapex import apex_email

from piktio.models import (
    DBSession,
    get_valid_game,
    copy_game_to_step,
    Subject,
    Predicate,
    Drawing,
    Description,
    Game,
    PiktioProfile,
    InviteAddress,
    Strikes,
    Rating
)
from piktio.storage import upload_photo
from piktio.forms import DisplayNameForm, InviteFriendForm
from piktio import serializers

from apex.models import (AuthID, AuthUser, AuthGroup)
from apex.lib.libapex import apex_settings, get_module, apex_remember
from apex import MessageFactory as _
from apex.lib.flash import flash

_ROW_LIMIT = 500


@view_config(route_name='home', renderer='templates/gameplay.html',
             permission='authenticated')
def home(request):
    render_context = {'user': request.user}
    return render_context


@view_config(route_name='games', renderer='templates/games.html',
             permission='view')
def games(request):
    completed_games = DBSession.query(Game)\
        .filter(~Game.time_completed.is_(None))\
        .order_by(Game.time_completed.desc()).limit(_ROW_LIMIT).all()
    render_context = {'user': request.user,
                      'collection': json.dumps(
                          serializers.game_list(completed_games, request))}
    return render_context


@view_config(route_name='game_list', renderer='json',
             permission='view')
def game_list(request):
    if request.matchdict['category'] == "all":
        completed_games = DBSession.query(Game)\
            .filter(~Game.time_completed.is_(None))\
            .order_by(Game.time_completed.desc()).limit(_ROW_LIMIT).all()
        return serializers.game_list(completed_games, request)
    if request.matchdict['category'] == "mine":
        if request.user is None:
            return {'error': 'please log in'}
        my_games = DBSession.query(Game)\
            .filter(~Game.time_completed.is_(None))\
            .filter(Game.authors.contains(request.user))\
            .order_by(Game.time_completed.desc()).limit(_ROW_LIMIT).all()
        return serializers.game_list(my_games, request)
    if request.matchdict['category'] == "friends":
        if request.user is None:
            return {'error': 'please log in'}
        friends_games = set()
        for friend in request.user.followees:
            friends_games = friends_games.union(
                DBSession.query(Game)
                         .filter(~Game.time_completed.is_(None))
                         .filter(Game.authors.contains(friend))
                         .all()
            )
        friends_games = list(friends_games)
        friends_games.sort(key=lambda gm: gm.time_completed)
        friends_games.reverse()
        return serializers.game_list(friends_games, request)


@view_config(route_name='follow', renderer='json', request_method='POST',
             permission='authenticated')
def follow(request):
    followee = DBSession.query(PiktioProfile).get(request.POST['id'])
    if (request.POST['followed'] == "true") \
            and (followee in request.user.followees):
        request.user.followees.remove(followee)
    if request.POST['followed'] == "false":
        request.user.followees.append(followee)
    return serializers.author(followee, request)


@view_config(route_name='game_by_id', renderer='json',
             permission='view')
def game_by_id(request):
    gm = DBSession.query(Game).get(request.matchdict['identifier'])
    return serializers.show_completed_game(gm, request)


# TODO: Make these all the same route, store step & game_id in session
@view_config(route_name='subject', renderer='json', request_method='POST',
             permission='authenticated')
def subject(request):
    # TODO: For all text entries, strip out carriage returns
    new_subject = Subject(author_id=request.user.id,
                          subject=request.POST['prompt'])
    DBSession.add(new_subject)
    DBSession.flush()
    new_game = Game(subject_id=new_subject.id)
    new_game.authors.append(request.user)
    DBSession.add(new_game)
    DBSession.flush()
    request.session['step'] = 'predicate'
    next_game = get_valid_game(request)

    return serializers.step(next_game, request)


@view_config(route_name='predicate', renderer='json', request_method='POST',
             permission='authenticated')
def predicate(request):
    new_predicate = Predicate(author_id=request.user.id,
                              predicate=request.POST['prompt'])
    DBSession.add(new_predicate)
    DBSession.flush()
    game = DBSession.query(Game).filter(
        Game.id == request.POST['game_id']).one()
    if game.predicate_id is not None:
        game = copy_game_to_step(game, 1)

    game.predicate_id = new_predicate.id

    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    request.session['step'] = 'first_drawing'
    next_game = get_valid_game(request)

    return serializers.step(next_game, request)


@view_config(route_name='first_drawing', renderer='json',
             request_method='POST', permission='authenticated')
def first_drawing(request):
    new_drawing_id = unicode(uuid.uuid4()) + u'.png'
    upload_photo(new_drawing_id, request.POST['drawing'])
    new_drawing = Drawing(author_id=request.user.id,
                          identifier=new_drawing_id)
    DBSession.add(new_drawing)
    DBSession.flush()

    game = DBSession.query(Game).filter(
        Game.id == request.POST['game_id']).one()
    if game.first_drawing_id is not None:
        game = copy_game_to_step(game, 2)

    game.first_drawing_id = new_drawing.id
    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    request.session['step'] = 'first_description'
    next_game = get_valid_game(request)

    return serializers.step(next_game, request)


@view_config(route_name='first_description', renderer='json',
             request_method='POST', permission='authenticated')
def first_description(request):
    new_description = Description(author_id=request.user.id,
                                  description=request.POST['prompt'])
    DBSession.add(new_description)
    DBSession.flush()
    game = DBSession.query(Game).filter(
        Game.id == request.POST['game_id']).one()
    if game.first_description_id is not None:
        game = copy_game_to_step(game, 3)

    game.first_description_id = new_description.id

    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    request.session['step'] = 'second_drawing'
    next_game = get_valid_game(request)

    return serializers.step(next_game, request)


@view_config(route_name='second_drawing', renderer='json',
             request_method='POST', permission='authenticated')
def second_drawing(request):
    new_drawing_id = unicode(uuid.uuid4()) + u'.png'
    upload_photo(new_drawing_id, request.POST['drawing'])
    new_drawing = Drawing(author_id=request.user.id,
                          identifier=new_drawing_id)
    DBSession.add(new_drawing)
    DBSession.flush()

    game = DBSession.query(Game).filter(
        Game.id == request.POST['game_id']).one()
    if game.second_drawing_id is not None:
        game = copy_game_to_step(game, 4)

    game.second_drawing_id = new_drawing.id
    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    request.session['step'] = 'second_description'
    next_game = get_valid_game(request)

    return serializers.step(next_game, request)


@view_config(route_name='second_description', renderer='json',
             request_method='POST', permission='authenticated')
def second_description(request):
    """The final step"""
    new_description = Description(author_id=request.user.id,
                                  description=request.POST['prompt'])
    DBSession.add(new_description)
    DBSession.flush()
    game = DBSession.query(Game).filter(
        Game.id == request.POST['game_id']).one()
    if game.second_description_id is not None:
        game = copy_game_to_step(game, 5)

    game.second_description_id = new_description.id

    game.authors.append(request.user)
    game.time_completed = datetime.datetime.now()
    DBSession.add(game)
    DBSession.flush()
    return {'info': 'Game completed',
            'redirect': request.route_path('games')
            }


@view_config(
    context='velruse.AuthenticationComplete',
)
def callback(request):
    user = None
    profile = request.context.profile
    if 'id' not in request.session:
        user = AuthUser.get_by_login(profile['preferredUsername'])
    if not user:
        if 'id' in request.session:
            auth_id = AuthID.get_by_id(request.session['id'])
        else:
            auth_id = AuthID()
            DBSession.add(auth_id)
        user = AuthUser(
            login=profile['preferredUsername'],
            provider=request.context.provider_name,
        )
        if 'verifiedEmail' in profile:
            user.email = profile['verifiedEmail']
        if 'displayName' in profile:
            user.display_name = profile['displayName']
            # TODO: This may not be unique, handle the error here.
        auth_id.users.append(user)
        DBSession.add(user)
        DBSession.flush()
        if apex_settings('default_user_group'):
            for name in apex_settings('default_user_group'). \
                    split(','):
                group = DBSession.query(AuthGroup). \
                    filter(AuthGroup.name == name.strip()).one()
                auth_id.groups.append(group)
        if apex_settings('create_openid_after'):
            openid_after = get_module(apex_settings('create_openid_after'))
            openid_after().after_signup(request=request, user=user)
        DBSession.flush()
    headers = apex_remember(request, user)
    redir = request.GET.get(
        'came_from',
        request.route_path(
            apex_settings('came_from_route')
        )
    )
    flash(_('Successfully Logged in, welcome!'), 'success')
    return HTTPFound(location=redir, headers=headers)


@view_config(route_name='change_name', renderer='templates/forms.html',
             permission='authenticated')
def change_name(request):
    form = DisplayNameForm(
        request.POST,
        captcha={'ip_address': request.environ['REMOTE_ADDR']}
    )

    if request.method == 'POST' and form.validate():
        request.user.display_name = form.data['display_name']
        return HTTPFound(location=request.route_path('home'))

    return {'title': 'Change your display name',
            'user': request.user,
            'form': form}


@view_config(route_name='invite', renderer='templates/forms.html',
             permission='authenticated')
def invite(request):
    form = InviteFriendForm(
        request.POST,
        captcha={'ip_address': request.environ['REMOTE_ADDR']}
    )

    if request.method == 'POST' and form.validate():
        new_invitation = InviteAddress(email=form.data['email_address'])
        body = form.data['email_body'] + """
_____
This message was sent to invite you to join piktio.com.
You will never receive email from this site again.
"""
        apex_email(request, recipients=form.data['email_address'],
                   subject=form.data['email_subject'], body=body)
        DBSession.add(new_invitation)
        flash(_('Invitation email sent.'))
        return HTTPFound(location=request.route_path('invite'))

    form.email_body.data = \
"""Hello,
    %s has invited you to join piktio.com. We hope to see you there!
""" % request.user.display_name

    return {'title': 'Invite someone to join piktio!',
            'user': request.user,
            'form': form}


@view_config(route_name='strike', renderer='json',
             permission='authenticated', request_method='POST')
def strike(request):
    """Add a strike to the prompt/drawing for this step, return a new prompt drawing"""
    game = DBSession.query(Game).filter(
        Game.id == request.POST['game_id']).one()
    if request.matchdict['step'] == 'first_drawing':
        subject_strike = Strikes()
        subject_strike.author = request.user
        subject_strike.subject = game.subject
        predicate_strike = Strikes()
        predicate_strike.author = request.user
        predicate_strike.predicate = game.predicate
        DBSession.add(subject_strike)
        DBSession.add(predicate_strike)
        request.session['step'] = 'first_drawing'
        next_game = get_valid_game(request)
        return serializers.step(next_game, request)

    if request.matchdict['step'] == 'first_description':
        drawing_strike = Strikes()
        drawing_strike.author = request.user
        drawing_strike.drawing = game.first_drawing
        DBSession.add(drawing_strike)
        request.session['step'] = 'first_description'
        next_game = get_valid_game(request)
        return serializers.step(next_game, request)

    if request.matchdict['step'] == 'second_drawing':
        description_strike = Strikes()
        description_strike.author = request.user
        description_strike.description = game.first_description
        DBSession.add(description_strike)
        request.session['step'] = 'second_drawing'
        next_game = get_valid_game(request)
        return serializers.step(next_game, request)

    if request.matchdict['step'] == 'second_description':
        drawing_strike = Strikes()
        drawing_strike.author = request.user
        drawing_strike.drawing = game.second_drawing
        DBSession.add(drawing_strike)
        request.session['step'] = 'second_description'
        next_game = get_valid_game(request)
        return serializers.step(next_game, request)


@view_config(route_name='rate', renderer='json',
             permission='authenticated', request_method='POST')
def rate(request):
    """Add a rating to a game, update ratings on page"""
    # TODO add validation to this POST (form?)
    game_id = request.POST['game_id']
    current_rating = DBSession.query(Rating).filter(
            Rating.game == game_id,
            Rating.rater == request.user.id
        ).first()
    if not current_rating:
        current_rating = Rating()
        current_rating.game = game_id
        current_rating.rater = request.user.id

    current_rating.rating = int(request.POST['author_score'])
    DBSession.add(current_rating)
    DBSession.flush()
    return serializers.rating(game_id, request)
