import unittest

from pyramid import testing
import transaction

from apex.models import AuthUser, AuthID
from piktio.models import (DBSession,
                           PiktioProfile,
                           Subject,
                           Predicate,
                           Game,
                           Strikes,
                           )
from webtest import TestApp
from piktio.forms import NewRegisterForm, create_user
# from apex.lib.libapex import create_user


class TestFunctionalLoginAndViews(unittest.TestCase):
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
        self.csrf = '123'
        settings = {'sqlalchemy.url': 'sqlite://',
                    'apex.session_secret': '${APEX_SESSION_SECRET}',
                    'apex.auth_secret': '${APEX_AUTH_SECRET}',
                    'apex.came_from_route': 'home',
                    'facebook.consumer_key': '${FACEBOOK_CONSUMER_KEY}',
                    'facebook.consumer_secret': '${FACEBOOK_CONSUMER_SECRET}',
                    'google.consumer_key': '${GOOGLE_CONSUMER_KEY}',
                    'google.consumer_secret': '${GOOGLE_CONSUMER_SECRET}',
                    'jinja2.filters': {
                        'route_path': 'pyramid_jinja2.filters:route_path_filter',
                        'static_path': 'pyramid_jinja2.filters:static_path_filter'},
                    'session.constant_csrf_token': self.csrf
                    }
        app = main({}, **settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_apex_overwrites_and_login(self):
        """Test my rewrites of apex functions & forms and that login works"""
        # Create a user
        testuser = {}
        testuser['password'] = "password"
        testuser['display_name'] = "Testy"
        with transaction.manager:
            dumdum = NewRegisterForm(obj=testuser)
            auth_id = create_user(username="test", password="password", display_name="Testy")
            dumdum.after_signup(auth_id)

        # AuthID, AuthUser, and PiktioProfile all created
        auth_id = DBSession.query(AuthID).first()
        user = DBSession.query(AuthUser).first()
        profile = DBSession.query(PiktioProfile).first()
        self.assertEqual(auth_id.id, user.auth_id)
        self.assertEqual(profile.auth_id, auth_id.id)
        self.assertEqual(profile.display_name, "Testy")
        self.assertEqual(user.login, "test")

        # Test login
        res = self.testapp.post('/auth/login', {'login': 'test',
                                                'password': 'password',
                                                'csrf_token': self.csrf})
        self.assertEqual(302, res.status_code)  # Redirect to home
        new_res = self.testapp.get('/')
        self.assertIn("Testy", new_res.body)  # Successfully logged in

        # Test logout
        self.testapp.get('/auth/logout')
        res = self.testapp.get('/')
        self.assertIn('/auth/login', res.body)  # Redirect to login

    def create_and_login_user(self,
                              username='test',
                              password='password',
                              display_name="Testy"):
        """Logs in. This is tested in the previous test"""
        testuser = {'password': password, 'display_name': display_name}
        with transaction.manager:
            dumdum = NewRegisterForm(obj=testuser)
            auth_id = create_user(username=username,
                                  password=password,
                                  display_name=display_name)
            dumdum.after_signup(auth_id)
        self.testapp.post('/auth/login', {'login': username,
                                          'password': password,
                                          'csrf_token': self.csrf})

    def login_user(self,
                   username='test',
                   password='password'):
        self.testapp.post('/auth/login', {'login': username,
                                          'password': password,
                                          'csrf_token': self.csrf})

    def test_post_subject(self):
        """Tests posting of first subject"""
        self.create_and_login_user()
        payload = {'prompt': "TEST SUBJECT",
                   'csrf_token': self.csrf}
        res = self.testapp.post('/subject', payload)
        self.assertEqual(res.status_code, 200)

        # No other subjects have been created, so:
        self.assertIn("No suitable game for the next step", res.body)
        subj = DBSession.query(Subject).one()
        self.assertEqual(subj.subject, "TEST SUBJECT")
        game = DBSession.query(Game).one()
        self.assertEqual(game.subject.subject, "TEST SUBJECT")
        author = DBSession.query(PiktioProfile).\
            filter(PiktioProfile.display_name == u"Testy").one()
        self.assertEqual(game.authors[0].id, author.id)
        transaction.commit()

        # Create another one as a different user and confirm we can add to the first
        self.testapp.get('/auth/logout')
        self.create_and_login_user(username="test2", display_name="TESTY 2")
        payload = {'prompt': "TEST SUBJECT 2",
                   'csrf_token': self.csrf}
        res = self.testapp.post('/subject', payload)
        subjs = DBSession.query(Subject).all()
        self.assertEqual(len(subjs), 2)
        self.assertNotEqual(subjs[0].author_id, subjs[1].author_id)
        self.assertEqual(res.status_code, 200)
        self.assertIn("predicate", res.body)
        self.assertNotIn("error", res.body)

    def test_post_predicate(self):
        import json
        self.create_and_login_user()  # Testy
        payload = {'prompt': "TEST SUBJECT",
                   'csrf_token': self.csrf}
        self.testapp.post('/subject', payload)
        firstgame_id = DBSession.query(Game).one().id
        firstsubj_id = DBSession.query(Subject).one().id
        transaction.commit()

        self.create_and_login_user(username="bacon", display_name="Bacon")
        payload['prompt'] = "Bacon bacon bacon"
        res = self.testapp.post('/subject', payload)
        bacon_load = json.loads(res.body)
        # Bacon is working on Testy's game
        self.assertEqual(bacon_load['game_id'], firstgame_id)
        transaction.commit()

        self.create_and_login_user(username="eggs", display_name="Eggs")
        payload['prompt'] = "eggs eggs eggs"
        res = self.testapp.post('/subject', payload)
        egg_load = json.loads(res.body)
        # Eggs is also working on Testy's game
        self.assertEqual(egg_load['game_id'], firstgame_id)
        transaction.commit()

        # Eggs submits a predicate
        egg_load['prompt'] = "egg predicate"
        res = self.testapp.post('/predicate', egg_load)
        self.assertIn("No suitable game for the next step", res.body)
        egg_pred = DBSession.query(Predicate).one()
        self.assertEqual(egg_pred.predicate, "egg predicate")
        # Remember the game Eggs submitted a predicate to:
        egg_game_id = egg_pred.games[0].id
        # It's still the game where Testy wrote the subject
        self.assertEqual(egg_game_id, firstgame_id)
        transaction.commit()

        # Bacon also submits a predicate to the same game
        self.login_user(username="bacon")
        bacon_load['prompt'] = "bacon predicate"
        res = self.testapp.post('/predicate', bacon_load)
        transaction.commit()
        # Now bacon gets to work on Test & Egg's game
        self.assertIn("TEST SUBJECT egg predicate", res.body)
        bacon_pred = DBSession.query(Predicate)\
            .filter(Predicate.predicate == "bacon predicate").one()
        bacon_game_id = bacon_pred.games[0].id

        # A copy has been made
        self.assertNotEqual(egg_game_id, bacon_game_id)
        games = DBSession.query(Game).all()
        self.assertEqual(len(games), 4)
        # With the same first subject in both
        firstsubj = DBSession.query(Subject).filter(Subject.id == firstsubj_id).one()
        self.assertEqual(len(firstsubj.games), 2)

    def test_post_strike(self):
        import json
        self.create_and_login_user()  # Testy
        payload = {'prompt': "TEST SUBJECT",
                   'csrf_token': self.csrf}
        self.testapp.post('/subject', payload)
        firstgame_id = DBSession.query(Game).one().id
        transaction.commit()

        self.create_and_login_user(username="bacon", display_name="Bacon")
        payload['prompt'] = "Bacon bacon bacon"
        res = self.testapp.post('/subject', payload)
        bacon_load = json.loads(res.body)
        # Bacon is working on Testy's game
        self.assertEqual(bacon_load['game_id'], firstgame_id)
        bacon_load['prompt'] = "bacon predicate"
        res = self.testapp.post('/predicate', bacon_load)
        transaction.commit()

        self.create_and_login_user(username="eggs", display_name="Eggs")
        payload['prompt'] = "eggs eggs eggs"
        res = self.testapp.post('/subject', payload)
        egg_load = json.loads(res.body)
        # Eggs is working on bacon's subject
        egg_load['prompt'] = "egg predicate"
        res = self.testapp.post('/predicate', egg_load)
        game_data = json.loads(res.body)
        # We are working on testy & bacon's prompt
        self.assertEqual(game_data['instructions'], 'TEST SUBJECT bacon predicate')
        res = self.testapp.post(game_data['route'] + '/strike', game_data)
        # That should add strikes from Eggs to Testy's subject and Bacon's predicate
        strikes = DBSession.query(Strikes).all()
        self.assertEqual(len(strikes), 2)
        self.assertEqual(strikes[0].subject.subject, "TEST SUBJECT")
        self.assertEqual(strikes[0].author.display_name, "Eggs")
        self.assertEqual(strikes[1].predicate.predicate, "bacon predicate")
        self.assertEqual(strikes[1].author.display_name, "Eggs")
        # There should be no available game anymore
        struck_response = json.loads(res.body)
        self.assertEqual(struck_response['error'], 'no suitable game')
