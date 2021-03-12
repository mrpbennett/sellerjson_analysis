from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class SubmitURL(FlaskForm):
    sellers_json_url = StringField("URL", validators=[DataRequired()])
    submit = SubmitField("pull data")