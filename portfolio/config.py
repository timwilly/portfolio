import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Charge le fichier .env et on utilise os.getenv('') pour récupérer les 
# variables
load_dotenv(os.path.join(basedir, '.env'))

# Jeu d'instruction qui sont défini AVANT que l'app soit en live
# object est passé ici pour passé de old-style class en new-style class
# c'était pour la conversion de python2 vers python3 mais nous n'avons
# plus nécessairement besoin d'adopter cette pratique en python3
class Config(object):
    # Si l'environnement ne définit pas de variable (configuré au terminal),
    # une clé de développement sera utilisée.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Localisation du database de l'application...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email à envoyer
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', '').lower() in \
                   ['true', '1', 'yes', 'on']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    ADMINS = ['projet.timwilly@gmail.com']
    POSTS_PER_PAGE = 10
    
    # pybabel
    LANGUAGES = {'en': 'English', 'fr': 'French', 'es': 'Español'}
    BABEL_DEFAULT_LOCALE = 'fr'

    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY') or \
                        os.getenv('MS_TRANSLATOR_KEY')
    
    ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL')
    
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    
    # json utf-8 avec indentation
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    SCHEDULER_API_ENABLED = True
    BUSINESS_IMPORT_SCHEDULER_ENABLED = os.environ.get(
        'BUSINESS_IMPORT_SCHEDULER_ENABLED', 'false'
    ).lower() in ['true', '1', 'yes', 'on']
    
    # TODO: À effacer à la fin !
    #for a in os.environ:
    #    print('Var: ', a, 'Value: ', os.getenv(a))
    #print("all done")
    # tweepy key & secret
    twitter_consumer_key = None
    twitter_consumer_secret = None
    twitter_access_token = None
    twitter_access_token_secret = None
