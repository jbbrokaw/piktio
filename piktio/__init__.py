from pyramid.config import Configurator
from pyramid.security import NO_PERMISSION_REQUIRED
from sqlalchemy import engine_from_config

import configure
import os
from .models import (
    DBSession,
    Base,
    )

from .views import callback


def expandvars_dict(settings):
    """Expands all environment variables in a settings dictionary."""
    return dict((key, os.path.expandvars(value)) for
                key, value in settings.iteritems())


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    configure.configure()
    settings = expandvars_dict(settings)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    # config.add_route('apex_callback', '/auth/apex_callback')
    # config.add_view(callback, route_name='apex_callback', permission=NO_PERMISSION_REQUIRED)
    config.include('apex', route_prefix='/auth')
    config.include('velruse.providers.facebook')
    config.add_facebook_login_from_settings(prefix='facebook.')
    # config.include('velruse.providers.google_oauth2')
    # config.add_facebook_login_from_settings(prefix='google.')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.scan()
    return config.make_wsgi_app()
