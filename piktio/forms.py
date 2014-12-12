from apex.forms import RegisterForm

from piktio.models import DBSession
from piktio.models import PiktioProfile

class NewRegisterForm(RegisterForm):
    def after_signup(self, user):
        DBSession.flush()
        profile = PiktioProfile(auth_id=user.id)
        DBSession.add(profile)
        DBSession.flush()
