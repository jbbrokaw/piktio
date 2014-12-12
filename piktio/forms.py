from apex.forms import RegisterForm

from piktio.models import PiktioProfile
from apex.models import DBSession, AuthID, AuthUser, AuthGroup
from apex import MessageFactory as _
from wtforms import StringField, validators
from sqlalchemy.orm.exc import NoResultFound


def create_user(**kwargs):
    """

::

    from apex.lib.libapex import create_user

    create_user(username='test', password='my_password', active='Y')

    Optional Parameters:

    display_name
    group



    Returns: AuthID object
    """
    auth_id = AuthID(active=kwargs.get('active', 'Y'))
    user = AuthUser(login=kwargs['username'], password=kwargs['password'],
                    active=kwargs.get('active', 'Y'))

    if 'display_name' in kwargs:
        user.display_name = kwargs['display_name']
        del kwargs['display_name']

    auth_id.users.append(user)

    if 'group' in kwargs:
        try:
            group = DBSession.query(AuthGroup).filter(AuthGroup.name == kwargs['group']).one()
            auth_id.groups.append(group)
        except NoResultFound:
            pass

        del kwargs['group']

    for key, value in kwargs.items():
        setattr(user, key, value)

    DBSession.add(auth_id)
    DBSession.add(user)
    DBSession.flush()
    return user

class NewRegisterForm(RegisterForm):
    display_name = StringField(_('Display Name'), [validators.DataRequired(),
                               validators.Length(min=4, max=25)])

    def after_signup(self, user):
        profile = PiktioProfile(auth_id=user.id, display_name=user.display_name)
        DBSession.add(profile)
        DBSession.flush()

    def create_user(self, login):
        group = self.request.registry.settings.get('apex.default_user_group',
                                                   None)
        user = create_user(username=login,
                           password=self.data['password'],
                           email=self.data['email'],
                           display_name=self.data['display_name'],
                           group=group)
        return user
