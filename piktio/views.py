from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url
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
import uuid

from apex.models import (AuthID, AuthUser, AuthGroup)

from apex.lib.libapex import apex_settings, get_module, apex_remember
from apex import MessageFactory as _


@view_config(route_name='home', renderer='templates/gameplay.html',
             permission='authenticated')
def home(request):
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
    request.response_status = '201 Created'  # THIS DOES NOT WORK
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
            'route': '/predicate',  # Replace this with route_url
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
    request.response_status = '201 Created'  # THIS DOES NOT WORK
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
            'route': '/first_drawing',  # Replace this with route_url
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
    request.response_status = '201 Created'  # THIS DOES NOT WORK
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
            'route': '/first_description',  # Replace this with route_url
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
    request.response_status = '201 Created'  # THIS DOES NOT WORK
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
            'route': '/second_drawing',  # Replace this with route_url
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
    request.response_status = '201 Created'  # THIS DOES NOT WORK
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
            'route': '/second_description',  # TODO: Replace this with route_url
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
    DBSession.add(game)
    DBSession.flush()
    request.response_status = '201 Created'  # THIS DOES NOT WORK
    return {'info': 'Game completed',
            'redirect': '/game/' + str(game.id)  # TODO: use route_url
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
        if profile.has_key('email'):
            user.email = profile['email']
        if profile.has_key('displayName'):
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
    if apex_settings('openid_required'):
        openid_required = False
        for required in apex_settings('openid_required').split(','):
            if not getattr(user, required):
                openid_required = True
        if openid_required:
            request.session['id'] = auth_id.id
            request.session['userid'] = user.id
            return HTTPFound(location='%s?came_from=%s' %
                                      (route_url('apex_openid_required', request),
                                       request.GET.get('came_from',
                                                       route_url(apex_settings('came_from_route'), request))))
    headers = apex_remember(request, user)
    redir = request.GET.get('came_from',
                            route_url(apex_settings('came_from_route'), request))
    flash(_('Successfully Logged in, welcome!'), 'success')
    return HTTPFound(location=redir, headers=headers)
