from flask_apscheduler import APScheduler
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_moment import Moment
from flask_migrate import Migrate
from flask_login import LoginManager

# Ici on retrouve les objets qui représente les extensions !
# (Extensions provenant seulement de flask !!)
# On les instancies ici de sorte que l'on peut créer plusieurs
# apps avec des configurations différentes pour tester ou autres
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()
login = LoginManager()
scheduler = APScheduler()