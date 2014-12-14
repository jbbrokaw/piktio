import unittest

from pyramid import testing

from .models import DBSession, PiktioProfile
from webtest import TestApp


class TestFunctionalLogin(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        from sqlalchemy import create_engine
        engine = create_engine('sqlite://')
        from .models import Base
        import apex.models
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        apex.models.Base.metadata.create_all(engine)
        DBSession.flush()
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

    def test_register(self):
        res = self.testapp.get('/auth/register', extra_environ={'REMOTE_ADDR': 'local.piktio.com'})
        csrf = res.form.fields['csrf_token'][0].value
        res = self.testapp.post('/auth/register',
            {
                'submit': True,
                'login': 'testy',
                'password': 'temp',
                'display_name': 'TESTY',
                'email': 'testy@testy.com',
                'csrf_token': csrf
            }, extra_environ={'REMOTE_ADDR': 'local.piktio.com'}
        )
        new_user = DBSession.query(PiktioProfile).filter(PiktioProfile.display_name == "TESTY").first()
        self.assertIsNotNone(new_user)
        self.assertEqual(200, res.status_code)

    def test_login(self):
        res = self.testapp.post('/auth/login', {'login': 'testy', 'password': 'temp'})
        self.assertIn('TESTY', res.body)
