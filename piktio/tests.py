import unittest

from pyramid import testing
import transaction

from apex.models import AuthUser, AuthID
from piktio.models import DBSession, PiktioProfile
from webtest import TestApp
from piktio.forms import NewRegisterForm, create_user
# from apex.lib.libapex import create_user


class TestFunctionalLogin(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        from sqlalchemy import create_engine
        engine = create_engine('sqlite://')
        from .models import Base
        import apex.models
        transaction.begin()
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        apex.models.Base.metadata.create_all(engine)
        DBSession.flush()
        transaction.commit()
        from piktio import main
        settings = {'sqlalchemy.url': 'sqlite://',
                    'apex.session_secret': '${APEX_SESSION_SECRET}',
                    'apex.auth_secret': '${APEX_AUTH_SECRET}',
                    'apex.came_from_route': 'home',
                    'facebook.consumer_key': '${FACEBOOK_CONSUMER_KEY}',
                    'facebook.consumer_secret': '${FACEBOOK_CONSUMER_SECRET}',
                    }
        app = main({}, **settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_apex_overwrites_and_login(self):
        """Test my rewrites of apex functions & forms and that login works"""
        testuser = {}
        testuser['password'] = "password"
        testuser['display_name'] = "Testy"
        with transaction.manager:
            dumdum = NewRegisterForm(obj=testuser)
            auth_id = create_user(username="test", password="password", display_name="Testy")
            dumdum.after_signup(auth_id)
        auth_id = DBSession.query(AuthID).first()
        user = DBSession.query(AuthUser).first()
        profile = DBSession.query(PiktioProfile).first()
        self.assertEqual(auth_id.id, user.auth_id)
        self.assertEqual(profile.auth_id, auth_id.id)
        self.assertEqual(profile.display_name, "Testy")
        self.assertEqual(user.login, "test")

        csrf_resp = self.testapp.get('/auth/login')
        csrf = csrf_resp.form.fields['csrf_token'][0].value
        res = self.testapp.post('/auth/login', {'login': 'test',
                                                'password': 'password',
                                                'csrf_token': csrf})
        self.assertEqual(302, res.status_code)
        new_res = self.testapp.get('/')
        self.assertIn("Testy", new_res.body)

    def test_post_subject(self):
        """Test my rewrites of apex functions & forms and that login works"""
        testuser = {}
        testuser['password'] = "password"
        testuser['display_name'] = "Testy"
        with transaction.manager:
            dumdum = NewRegisterForm(obj=testuser)
            auth_id = create_user(username="test",
                                  password="password",
                                  display_name="Testy")
            dumdum.after_signup(auth_id)
        csrf_resp = self.testapp.get('/auth/login')
        csrf = csrf_resp.form.fields['csrf_token'][0].value
        res = self.testapp.post('/auth/login', {'login': 'test',
                                                'password': 'password',
                                                'csrf_token': csrf})
        new_res = self.testapp.post('/subject', {'dummy': 'data'})
        print value
