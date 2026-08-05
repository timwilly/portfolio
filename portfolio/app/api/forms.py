from app.models import User
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo


class SearchForm(FlaskForm):
    search = StringField(_l('Search'), validators=[DataRequired()],
                         id='business_autocomplete')
    submit = SubmitField(_l('Submit'))