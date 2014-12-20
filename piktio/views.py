import uuid
import datetime

from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound
from apex.lib.flash import flash

from piktio.models import (
    DBSession,
    copy_game_to_step,
    Subject,
    Predicate,
    Drawing,
    Description,
    Game,
)
from piktio.storage import upload_photo

from apex.models import (AuthID, AuthUser, AuthGroup)

from apex.lib.libapex import apex_settings, get_module, apex_remember
from apex import MessageFactory as _


@view_config(route_name='home', renderer='templates/gameplay.html',
             permission='authenticated')
def home(request):
    render_context = {'user': request.user}
    return render_context


@view_config(route_name='games', renderer='templates/games.html',
             permission='view')
def games(request):
    render_context = {'user': request.user}
    return render_context


@view_config(route_name='game_list', renderer='json',
             permission='view')
def game_list(request):
    response = [{'id': 1}]
    return response


@view_config(route_name='game_by_id', renderer='json',
             permission='view')
def game_by_id(request):
    response = {'id': request.matchdict['identifier']}
    return response


@view_config(route_name='games', renderer='templates/games.html',
             permission='view')
def games(request):
    context = {'user': request.user}
    return context



@view_config(route_name='subject', renderer='json', request_method='POST',
             permission='authenticated')
def subject(request):
    new_subject = Subject(author_id=request.user.id,
                          subject=request.POST['prompt'])
    DBSession.add(new_subject)
    DBSession.flush()
    new_game = Game(subject_id=new_subject.id)
    new_game.authors.append(request.user)
    DBSession.add(new_game)
    DBSession.flush()
    next_game = DBSession.query(Game).filter(Game.predicate_id.is_(None))\
            .filter(~Game.authors.contains(request.user)).first()
    if next_game is None:
        return {'error': 'No suitable game for the next step'}
    instructions = 'Like "disguised himself as a raincloud ' \
                   'to steal honey from the tree"'
    csrf = request.session.new_csrf_token()
    return {'title': 'Enter the predicate of a sentence',
            'instructions': instructions,
            'game_id': next_game.id,
            'authors': [{'id': auth.id,
                         'display_name': auth.display_name,
                         'followed': (auth in request.user.followees)}
                        for auth in next_game.authors],
            'route': request.route_path('predicate'),
            'csrf_token': csrf
            }

@view_config(route_name='predicate', renderer='json', request_method='POST',
             permission='authenticated')
def predicate(request):
    new_predicate = Predicate(author_id=request.user.id,
                              predicate=request.POST['prompt'])
    DBSession.add(new_predicate)
    DBSession.flush()
    game = DBSession.query(Game).filter(Game.id == request.POST['game_id']).one()
    if game.predicate_id is not None:
        game = copy_game_to_step(game, 1)

    game.predicate_id = new_predicate.id

    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    next_game = DBSession.query(Game)\
        .filter(~Game.predicate_id.is_(None))\
        .filter(Game.first_drawing_id.is_(None))\
        .filter(~Game.authors.contains(request.user)).first()
    if next_game is None:
        return {'error': 'No suitable game for the next step'}
    instructions = " ".join([next_game.subject.subject,
                             next_game.predicate.predicate])
    csrf = request.session.new_csrf_token()
    return {'title': 'Draw this sentence',
            'instructions': instructions,
            'game_id': next_game.id,
            'authors': [{'id': auth.id,
                         'display_name': auth.display_name,
                         'followed': (auth in request.user.followees)}
                        for auth in next_game.authors],
            'route': request.route_path('first_drawing'),
            'csrf_token': csrf
            }


@view_config(route_name='first_drawing', renderer='json', request_method='POST',
             permission='authenticated')
def first_drawing(request):
    new_drawing_id = unicode(uuid.uuid4()) + u'.png'
    upload_photo(new_drawing_id, request.POST['drawing'])
    new_drawing = Drawing(author_id=request.user.id,
                          identifier=new_drawing_id)
    DBSession.add(new_drawing)
    DBSession.flush()

    game = DBSession.query(Game).filter(Game.id == request.POST['game_id']).one()
    if game.first_drawing_id is not None:
        game = copy_game_to_step(game, 2)

    game.first_drawing_id = new_drawing.id
    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    next_game = DBSession.query(Game)\
        .filter(~Game.first_drawing_id.is_(None))\
        .filter(Game.first_description_id.is_(None))\
        .filter(~Game.authors.contains(request.user)).first()
    if next_game is None:
        return {'error': 'No suitable game for the next step'}
    csrf = request.session.new_csrf_token()
    return {'title': 'Describe this drawing',
            'instructions': 'Try to make it fun to draw',
            'game_id': next_game.id,
            'drawing': next_game.first_drawing.identifier,
            'authors': [{'id': auth.id,
                         'display_name': auth.display_name,
                         'followed': (auth in request.user.followees)}
                        for auth in next_game.authors],
            'route': request.route_path('first_description'),
            'csrf_token': csrf
            }


@view_config(route_name='first_description', renderer='json', request_method='POST',
             permission='authenticated')
def first_description(request):
    new_description = Description(author_id=request.user.id,
                                  description=request.POST['prompt'])
    DBSession.add(new_description)
    DBSession.flush()
    game = DBSession.query(Game).filter(Game.id == request.POST['game_id']).one()
    if game.first_description_id is not None:
        game = copy_game_to_step(game, 3)

    game.first_description_id = new_description.id

    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    next_game = DBSession.query(Game)\
        .filter(~Game.first_description_id.is_(None))\
        .filter(Game.second_drawing_id.is_(None))\
        .filter(~Game.authors.contains(request.user)).first()
    if next_game is None:
        return {'error': 'No suitable game for the next step'}
    csrf = request.session.new_csrf_token()
    return {'title': 'Draw this sentence',
            'instructions': next_game.first_description.description,
            'game_id': next_game.id,
            'authors': [{'id': auth.id,
                         'display_name': auth.display_name,
                         'followed': (auth in request.user.followees)}
                        for auth in next_game.authors],
            'route': request.route_path('second_drawing'),
            'csrf_token': csrf
            }


@view_config(route_name='second_drawing', renderer='json', request_method='POST',
             permission='authenticated')
def second_drawing(request):
    new_drawing_id = unicode(uuid.uuid4()) + u'.png'
    upload_photo(new_drawing_id, request.POST['drawing'])
    new_drawing = Drawing(author_id=request.user.id,
                          identifier=new_drawing_id)
    DBSession.add(new_drawing)
    DBSession.flush()

    game = DBSession.query(Game).filter(Game.id == request.POST['game_id']).one()
    if game.second_drawing_id is not None:
        game = copy_game_to_step(game, 4)

    game.second_drawing_id = new_drawing.id
    game.authors.append(request.user)
    DBSession.add(game)
    DBSession.flush()
    next_game = DBSession.query(Game)\
        .filter(~Game.second_drawing_id.is_(None))\
        .filter(Game.second_description_id.is_(None))\
        .filter(~Game.authors.contains(request.user)).first()
    if next_game is None:
        return {'error': 'No suitable game for the next step'}
    csrf = request.session.new_csrf_token()
    return {'title': 'Describe this drawing',
            'instructions': 'Try to make it fun to draw',
            'game_id': next_game.id,
            'drawing': next_game.second_drawing.identifier,
            'authors': [{'id': auth.id,
                         'display_name': auth.display_name,
                         'followed': (auth in request.user.followees)}
                        for auth in next_game.authors],
            'route': request.route_path('second_description'),
            'csrf_token': csrf
            }


@view_config(route_name='second_description', renderer='json', request_method='POST',
             permission='authenticated')
def second_description(request):
    """The final step"""
    new_description = Description(author_id=request.user.id,
                                  description=request.POST['prompt'])
    DBSession.add(new_description)
    DBSession.flush()
    game = DBSession.query(Game).filter(Game.id == request.POST['game_id']).one()
    if game.second_description_id is not None:
        game = copy_game_to_step(game, 5)

    game.second_description_id = new_description.id

    game.authors.append(request.user)
    game.time_completed = datetime.datetime.now()
    DBSession.add(game)
    DBSession.flush()
    return {'info': 'Game completed',
            'redirect': '/games/'  # TODO: use request.route_path
            }


# Just for DEBUG, DELETE THIS FOR PRODUCTION
# @forbidden_view_config(renderer='json')
# def forbidden(request):
#     return {'forbidden': request.exception.message}


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
        if 'email' in profile:
            user.email = profile['email']
        if 'displayName' in profile:
            user.display_name = profile['displayName']
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
    redir = request.GET.get('came_from',
                            request.route_path(
                                apex_settings('came_from_route'),
                                request)
                            )
    flash(_('Successfully Logged in, welcome!'), 'success')
    return HTTPFound(location=redir, headers=headers)
