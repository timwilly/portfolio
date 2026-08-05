from flask import render_template
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    # Si jamais ça change quelque chose dans la 'db' qui 
    # ne fonctionnerait pas, on retourne à un état précédent
    db.session.rollback()
    return render_template('errors/500.html'), 500