from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, DateTimeField, SelectField
from wtforms.validators import DataRequired, URL
from notion.client import NotionClient

import os

# session['connected'] = False

class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class NotionLocation(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), URL()])
    token = StringField('v2 Token')
    submit = SubmitField('Submit')

app = Flask(__name__)
app.config.from_object(Config)

def connect_notion(url, token):
    if token == "":
        token = "BOT_TOKEN"
    client = NotionClient(token_v2=token)
    view = client.get_collection_view(url)
    return view.collection

def make_full_form(schema):
    #Put all columns into  a field
    fields = dict()
    for column in schema:
        if column['type'] == 'title' or column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[])
        elif column['type'] == 'checkbox':
            fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
        elif column['type'] == 'date':
            fields[ column['slug'] ] = DateTimeField(column['name'], validators=[])
        elif column['type'] == 'select':
            fields[ column['slug'] ] = SelectField(column['name'], validators=[], choices=[("test", "test"), ("hi", "hi")])
        # elif column['type'] == 'multi_select':
        #     fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
    #make temporary class to hold our form
    class FullForm(NotionLocation):
        pass
    #apply all attributes of our temporary form
    for k, v in fields.items():
        setattr(FullForm, k, v)

    return FullForm()

@app.route("/", methods=['GET', 'POST'])
def home():
    form = NotionLocation()

    # If they put in good parameters and haven't connected yet
    if form.validate_on_submit() and session['connected'] == False:
        #see if what they gave us works
        try:
            collection = connect_notion(form.url.data, form.token.data)
            session['connected'] = True
        except Exception as e:
            #if we fail to connect, flash message and render OG form
            flash(e)
            return render_template('home.html', form=form)

        #if we connected properly
        full_form = make_full_form(collection.get_schema_properties())
        return render_template('home.html', form=full_form)

    # If they put in good parameters and have already connected
    if session.get('connected') == True:
        #pull columns out of notions to fill full form
        collection = connect_notion(form.url.data, form.token.data)
        full_form = make_full_form(collection.get_schema_properties())

        if form.validate_on_submit(): 
            ##TODO:  push it to notion!
            flash(f"INSERTED: {full_form.data}")

            #empty slots we don't want to reuse
            for field in full_form:
                if field.name not in ["url", "token"]:# and field.widget.input_type != 'hidden':
                    field.data = ""

            return render_template('home.html', form=full_form)

        return render_template('home.html', form=full_form)

    #Just starting or bad input
    session['connected'] = False
    return render_template('home.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
