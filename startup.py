from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import Form, SubmitField, StringField
from wtforms.validators import DataRequired, URL

import os

# session['connected'] = False

class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class NotionLocation(FlaskForm):
    link = StringField('URL', validators=[DataRequired(), URL()])
    token = StringField('v2 Token')
    submit = SubmitField('Submit')

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/", methods=['GET', 'POST'])
def home():
    form = NotionLocation()

    # If they put in good parameters and haven't connected yet
    if form.validate_on_submit() and session['connected'] == False:
        #see if what they gave us works
        try:
            ##TODO:  try to connect here
            session['connected'] = True
        except:
            #if we fail to connect, flash message and render OG form
            flash("Input Parameters don't seem to work!")
            return render_template('home.html', form=form)

        #if we connected properly
        ##TODO:  pull columns out of notions to fill full form
        class FullForm(NotionLocation):
            column = StringField('Some Column')
        new_form = FullForm()
        return render_template('home.html', form=new_form)

    # If they put in good parameters and have already connected
    if form.validate_on_submit() and session['connected'] == True:
        ##TODO:  pull columns out of notions to fill full form
        class FullForm(NotionLocation):
            column = StringField('Some Column')
        new_form = FullForm()

        ##TODO:  push it to notion!
        flash(f"INSERTED: {new_form.column.data}")

        #empty slots we don't want to reuse
        for field in new_form:
            if field.name not in ["link", "token"] and field.widget.input_type != 'hidden':
                field.data = ""

        return render_template('home.html', form=new_form)

    #Just starting or bad input
    session['connected'] = False
    return render_template('home.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
