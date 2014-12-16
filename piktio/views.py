from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.url import route_url
from apex.lib.flash import flash
from pyramid.security import NO_PERMISSION_REQUIRED

from .models import (
    DBSession,
    PiktioProfile,
)

from apex.models import (AuthID, AuthUser, AuthGroup)

from apex.lib.libapex import apex_settings, get_module, apex_remember
from apex import MessageFactory as _


@view_config(route_name='home', renderer='templates/step_one.html',
             permission='authenticated')
def home(request):
    context = {'user': request.user}
    return context


@view_config(route_name='subject', renderer='json', request_method='POST',
             permission='authenticated')
def subject(request):
    return {'message': 'success', 'user': request.user.display_name, 'user_id': request.user.id}


@forbidden_view_config(renderer='json')
def forbidden(request):
    return {'forbidden': request.exception.message}

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
