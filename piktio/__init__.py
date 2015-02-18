from pyramid.config import Configurator

import configure
import os
from piktio.models import (
    DBSession,
    PiktioProfile
)


def expandvars_dict(settings):
    """Expands all environment variables in a settings dictionary."""
    return dict((key, os.path.expandvars(value)) for
                key, value in settings.iteritems())


def get_user(request):
    user_id = request.authenticated_userid
    if user_id:
        user = DBSession.query(PiktioProfile) \
            .filter(PiktioProfile.auth_id == user_id) \
            .one()
    else:
        user = None
    return user


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    configure.configure()
    settings = expandvars_dict(settings)
    # Letting APEX do DB stuff
    # engine = engine_from_config(settings, 'sqlalchemy.')
    # DBSession.configure(bind=engine)
    # Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('pyramid_mako')
    config.include('pyramid_beaker')
    config.commit()
    config.add_jinja2_renderer('.html')
    config.add_request_method('piktio.get_user', 'user', reify=True)
    config.include('velruse.providers.facebook')
    config.add_facebook_login_from_settings(prefix='facebook.')
    config.include('velruse.providers.google_oauth2')
    config.add_google_oauth2_login_from_settings(prefix='google.')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('subject', '/subject')
    config.add_route('predicate', '/predicate')
    config.add_route('first_drawing', '/first_drawing')
    config.add_route('first_description', '/first_description')
    config.add_route('second_drawing', '/second_drawing')
    config.add_route('second_description', '/second_description')
    config.add_route('games', '/games')
    config.add_route('game_list', '/games/{category:all|mine|friends}')
    config.add_route(
        'game_by_id',
        '/games/{category:all|mine|friends}/{identifier}'
    )
    config.add_route('follow', '/follow')
    config.add_route('change_name', '/display_name')
    config.add_route('invite', '/invite')
    config.add_route(
        'strike',
        '/{step:first_drawing|first_description|second_drawing|second_description}/strike')
    config.include('apex', route_prefix='/auth')
    config.scan()
    return config.make_wsgi_app()
