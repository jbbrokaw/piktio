from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url
from sqlalchemy.exc import DBAPIError
from apex.lib.flash import flash

from .models import (
    DBSession,
    PiktioProfile,
)

from apex.models import (AuthID, AuthUser, AuthGroup)

from apex.lib.libapex import apex_settings, get_module, apex_remember
from apex import MessageFactory as _


@view_config(route_name='home', renderer='templates/step_one.html')
def home(request):
    context = {'user': request.user}
    return context


@view_config(
    context='velruse.AuthenticationComplete',
)
def callback(request):
    user = None
    profile = request.context.profile
    if not request.session.has_key('id'):
        user = AuthUser.get_by_login(profile['preferredUsername'])
    if not user:
        if request.session.has_key('id'):
            id = AuthID.get_by_id(request.session['id'])
        else:
            id = AuthID()
            DBSession.add(id)
        user = AuthUser(
            login=profile['preferredUsername'],
            provider=request.context.provider_name,
        )
        if profile.has_key('email'):
            user.email = profile['email']
        if profile.has_key('displayName'):
            user.display_name = profile['displayName']
        id.users.append(user)
        DBSession.add(user)
        DBSession.flush()
        if apex_settings('default_user_group'):
            for name in apex_settings('default_user_group'). \
                    split(','):
                group = DBSession.query(AuthGroup). \
                    filter(AuthGroup.name == name.strip()).one()
                id.groups.append(group)
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
            request.session['id'] = id.id
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


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_piktio_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

