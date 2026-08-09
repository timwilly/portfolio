import os
os.environ['DATABASE_URL'] = 'sqlite://' # Utilise une autre bd que l'original

import csv
import tempfile
import unittest
from app import create_app, db
from app.models import BusinessMontreal, User, Post
from app.tasks import import_businesses_once, refresh_businesses_once
from config import Config
from datetime import datetime, timedelta

class TestConfig(Config):
    # TESTING détermine si ça roule au travers des tests unitaire ou non...
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class UserModelCase(unittest.TestCase):
    # SetUp et tearDown sont des fonctions exécuté après chaque test unitaires
    def setUp(self):
        self.app = create_app(TestConfig)
        # Crée une application contexte pour les tests unitaires pour que 
        # db.create_all() puisse utiliser current_app.config pour trouver
        # où se trouve la db
        self.app_context = self.app.app_context()   # Établit un context
        self.app_context.push()                     # Push context dans stack
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()                      # Retire le context du stack
    
    def test_password_hashing(self):
        u = User(username = 'susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username = 'john', email = 'john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&f=y&s=128'))

    def test_home_is_public_and_protected_pages_redirect_to_login(self):
        client = self.app.test_client()

        response = client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/about_me'))
        with client.session_transaction() as session:
            self.assertNotIn('_flashes', session)

        response = client.get('/index')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])

    def test_feed_and_explore_navigation_requires_authentication(self):
        client = self.app.test_client()

        response = client.get('/about_me')
        self.assertNotIn(b'href="/index"', response.data)
        self.assertNotIn(b'href="/explore"', response.data)

        user = User(username='willy', email='willy@example.com')
        user.set_password('test')
        db.session.add(user)
        db.session.commit()

        login_response = client.post('/auth/login', data={
            'username': 'willy',
            'password': 'test'
        })
        self.assertEqual(login_response.status_code, 302)

        response = client.get('/about_me')
        self.assertIn(b'href="/index"', response.data)
        self.assertIn(b'href="/explore"', response.data)

    def test_profile_picture_upload_is_disabled(self):
        client = self.app.test_client()
        user = User(username='willy', email='willy@example.com')
        user.set_password('test')
        db.session.add(user)
        db.session.commit()

        client.post('/auth/login', data={
            'username': 'willy',
            'password': 'test'
        })
        response = client.get('/edit_profile')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'type="file"', response.data)
    
    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from john", author=u1,
                  timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2,
                  timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from mary", author=u3,
                  timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

    def test_import_businesses_once(self):
        old_update = datetime(2020, 1, 1)
        db.session.add_all([
            BusinessMontreal(
                id=1, name='Ancien nom', address='1 Rue A', city='Montreal',
                state='Quebec', type='Restaurant', statut='Ouvert',
                date_statut=datetime(2020, 1, 1).date(), latitude=45.0,
                longitude=-73.0, x=1.0, y=2.0,
                date_last_update=old_update
            ),
            BusinessMontreal(
                id=2, name='A supprimer', address='2 Rue B', city='Montreal',
                state='Quebec', type='Restaurant', statut='Ouvert',
                date_statut=datetime(2020, 1, 1).date(), latitude=45.1,
                longitude=-73.1, x=3.0, y=4.0,
                date_last_update=old_update
            )
        ])
        db.session.commit()

        fieldnames = [
            'business_id', 'name', 'address', 'city', 'state', 'type',
            'statut', 'date_statut', 'latitude', 'longitude', 'x', 'y'
        ]
        rows = [
            {
                'business_id': '1', 'name': 'Nouveau nom',
                'address': '1 Rue A', 'city': 'Montreal', 'state': 'Quebec',
                'type': 'Restaurant', 'statut': 'Ouvert',
                'date_statut': '20240101', 'latitude': '45.0',
                'longitude': '-73.0', 'x': '1.0', 'y': '2.0'
            },
            {
                'business_id': '3', 'name': 'Nouvel établissement',
                'address': '3 Rue C', 'city': 'Montreal', 'state': 'Quebec',
                'type': 'Épicerie', 'statut': 'Ouvert',
                'date_statut': '20240202', 'latitude': '45.2',
                'longitude': '-73.2', 'x': '5.0', 'y': '6.0'
            }
        ]

        csv_file = tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', newline='', suffix='.csv',
            delete=False
        )
        try:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            csv_file.close()

            dry_result = import_businesses_once(
                csv_file.name, dry_run=True, minimum_rows=1
            )
            self.assertEqual(dry_result['created'], 1)
            self.assertEqual(dry_result['updated'], 1)
            self.assertEqual(dry_result['deleted'], 1)
            self.assertEqual(BusinessMontreal.query.count(), 2)
            self.assertEqual(
                db.session.get(BusinessMontreal, 1).name,
                'Ancien nom'
            )

            result = import_businesses_once(
                csv_file.name, minimum_rows=1
            )
            self.assertEqual(result['created'], 1)
            self.assertEqual(result['updated'], 1)
            self.assertEqual(result['deleted'], 1)
            self.assertEqual(
                [business.id for business in
                 BusinessMontreal.query.order_by(BusinessMontreal.id).all()],
                [1, 3]
            )
            self.assertEqual(
                db.session.get(BusinessMontreal, 1).name,
                'Nouveau nom'
            )
            self.assertIsNone(db.session.get(BusinessMontreal, 2))
        finally:
            csv_file.close()
            os.unlink(csv_file.name)

    def test_refresh_businesses_once_downloads_then_imports(self):
        fieldnames = [
            'business_id', 'name', 'address', 'city', 'state', 'type',
            'statut', 'date_statut', 'latitude', 'longitude', 'x', 'y'
        ]
        row = {
            'business_id': '10', 'name': 'Entreprise téléchargée',
            'address': '10 Rue Test', 'city': 'Montreal', 'state': 'Quebec',
            'type': 'Restaurant', 'statut': 'Ouvert',
            'date_statut': '20260804', 'latitude': '45.5',
            'longitude': '-73.5', 'x': '10.0', 'y': '20.0'
        }
        source_file = tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', newline='', suffix='.csv',
            delete=False
        )
        destination_file = tempfile.NamedTemporaryFile(
            suffix='.csv', delete=False
        )
        try:
            writer = csv.DictWriter(source_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)
            source_file.close()
            destination_file.close()

            result = refresh_businesses_once(
                csv_path=destination_file.name,
                source_url='file://' + source_file.name,
                minimum_rows=1
            )

            self.assertEqual(result['source_rows'], 1)
            self.assertEqual(result['created'], 1)
            self.assertEqual(BusinessMontreal.query.count(), 1)
            self.assertEqual(
                db.session.get(BusinessMontreal, 10).name,
                'Entreprise téléchargée'
            )
            with open(destination_file.name, encoding='utf-8') as saved_file:
                self.assertIn('Entreprise téléchargée', saved_file.read())
        finally:
            source_file.close()
            destination_file.close()
            os.unlink(source_file.name)
            os.unlink(destination_file.name)

if __name__ == '__main__':
    unittest.main(verbosity=2)
