from flask import Flask, render_template, flash, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import Form, SubmitField, StringField
from wtforms.validators import DataRequired, URL

import os

DEBUG = False

class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class NotionLocation(FlaskForm):
    link = StringField('URL', validators=[DataRequired(), URL()])
    token = StringField('v2 Token')
    submit = SubmitField('Get Access')

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/", methods=['GET', 'POST'])
def home():
    form = NotionLocation()
    if form.validate_on_submit():
        flash("Checking for connection...")
        return redirect(url_for("submit", form=form))
    # Debugging
    elif DEBUG:
        flash(form.errors)
    return render_template('home.html', form=form)

@app.route("/submit")
def submit():
    form = request.args['form']
    return type(form)


if __name__ == '__main__':
    app.run(debug=True)
