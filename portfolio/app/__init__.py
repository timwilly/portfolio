import folium
import logging
import os
import tweepy
import rq
import subprocess
from app.shared import db, migrate, mail, bootstrap, moment, babel, login, \
                       scheduler
from app.bgscheduler import scheduler
from config import Config
from elasticsearch import Elasticsearch
from flask import Flask, request, current_app, session
from flask_babel import lazy_gettext as _l
from logging.handlers import SMTPHandler, RotatingFileHandler
from redis import Redis


# Un contexte d'application doit exister pour utiliser l'application crée
def create_app(config_class=Config):
    # __name__ : nom du module qui est 'app'. 'app' ici est une instance 
    # de la classe Flask qui créer l'application simplement
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)
    register_extensions(app)
    
    # L'url 'login' si n'est pas connecté
    login.login_view = 'about_me.about_me'
    login.login_message = _l('Please log in to access this page.')
    
    m = folium.Map(location=[45.5236, -122.6750])
    app.redis = Redis.from_url(app.config['REDIS_URL'])    
    app.task_queue = rq.Queue('portfolio-tasks', connection=app.redis)

    # Instancie elasticsearch ici car ce n'est pas une extension flask
    # et nous avons besoin de l'app.config pour pouvoir l'initialiser
    # L'argument permet d'établir la connection...
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

    # Quand un blueprint est enregistré, ceci est connecté avec l'application..
    # L'importation est fait juste en haut de 'app.register_blueprint()' pour 
    # éviter la dépendance circulaire
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.about_me import bp as about_me_bp
    app.register_blueprint(about_me_bp)
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Le scheduler d'import est désactivé par défaut pour les opérations manuelles.
    if app.config['BUSINESS_IMPORT_SCHEDULER_ENABLED'] and \
            not app.testing and not scheduler.running:
        scheduler.start()
    
    # Importe les données, à enlever lors de la mise en production
    #from app.tasks import import_data_business_montreal
    #@app.before_first_request
    #def test():
    #   import_data_business_montreal()

    #from app.tasks import clear_users_related_tables
    #@app.before_first_request
    #def test2():
    #    clear_users_related_tables()

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost = (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr = 'no-reply@' + app.config['MAIL_SERVER'],
                toaddrs = app.config['ADMINS'], subject='Project Failure',
                credentials = auth, secure = secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/project.log', maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Project startup')

    return app

def register_extensions(app):
    # Applique l'instance d'extension dans l'application
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    login.init_app(app)
    scheduler.init_app(app)
    

@babel.localeselector
def get_locale():
    # Si l'utilisateur utilise un langage manuel du fureteur, il sera 
    # utilisé à l'intérieur de la session que nous utiliserons
    try:
        language = session['language']
    except KeyError:
        language = None
    if language is not None:
        return language
    return request.accept_languages.best_match(current_app.config['LANGUAGES'].keys())


# L'importation de models ici évite le phénomène d'importations
# circulaires
from app import models
