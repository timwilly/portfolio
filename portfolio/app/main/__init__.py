from flask import Blueprint

bp = Blueprint('main', __name__)

# En bas pour éviter les dépendances circulaires...
from app.main import routes