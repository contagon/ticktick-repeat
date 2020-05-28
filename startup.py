from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, SelectField, FileField, HiddenField
from wtforms.fields.html5 import DateField, TimeField, URLField, DecimalRangeField, EmailField, TelField
from wtforms.validators import DataRequired, URL
from notion.client import NotionClient

import os

# form.connected.data = False

##################################################
##########       SETTING UP FLASK       ##########
##################################################
class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class ConnectionForm(FlaskForm):
    db_url = StringField('URL', validators=[DataRequired(), URL()])
    token = StringField('v2 Token')
    submit = SubmitField('Submit')
    connected = HiddenField("Connected", default=False)

app = Flask(__name__)
app.config.from_object(Config)

##################################################
########   CONNECTING TO NOTION & FORMS   ########
##################################################
def connect_notion(db_url, token):
    if token == "":
        token = "blank"
    client = NotionClient(token_v2=token)
    view = client.get_collection_view(db_url)
    return view.collection

def make_full_form(schema):
    #Put all columns into  a field
    fields = dict()
    for column in schema:
        if column['type'] == 'title' or column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[])
        elif column['type'] == 'email':
            fields[ column['slug'] ] = EmailField(column['name'], validators=[])
        elif column['type'] == 'date':
            fields[ column['slug'] ] = DateField(column['name'], validators=[])
        elif column['type'] == 'url':
            fields[ column['slug'] ] = URLField(column['name'], validators=[])
        # elif column['type'] == 'person':
        #     fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
        elif column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[])
        elif column['type'] == 'phone_number':
            fields[ column['slug'] ] = TelField(column['name'], validators=[])
        elif column['type'] == 'select':
            options = [(i['id'], i['value']) for i in column['options']]
            fields[ column['slug'] ] = SelectField(column['name'], validators=[], choices=options)
        elif column['type'] == 'number':
            fields[ column['slug'] ] = DecimalRangeField(column['name'], validators=[])
        elif column['type'] == 'checkbox':
            fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
        # elif column['type'] == 'multi_select':
        #     fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
        # elif column['type'] == 'file':
        #     fields[ column['slug'] ] = FileField(column['name'], validators=[])
        # elif column['type'] == 'relation':
        #     fields[ column['slug'] ] = BooleanField(column['name'], validators=[])

    #make temporary class to hold our form
    class NotionForm(ConnectionForm):
        pass
    #apply all attributes of our temporary form
    for k, v in fields.items():
        setattr(NotionForm, k, v)

    return NotionForm()

##################################################
########              PAGES               ########
##################################################
@app.route("/", methods=['GET', 'POST'])
def home():
    form = ConnectionForm()

    #****************** CONNECTION FORM ******************
    print(form.connected.data)
    if form.validate_on_submit() and form.connected.data == "False":
        #see if what they gave us works
        try:
            collection = connect_notion(form.db_url.data, form.token.data)
            form.connected.data = "True"

        except Exception as e:
            #if we fail to connect, flash message and render OG form
            flash(e)
            return render_template('home.html', form=form)

        #if we connected properly, give them notion form
        full_form = make_full_form(collection.get_schema_properties())
        return render_template('home.html', form=full_form)


    #******************* NOTION FORM *******************
    if form.connected.data == "True":
        #pull columns out of notion to make notion form
        collection = connect_notion(form.db_url.data, form.token.data)
        full_form = make_full_form(collection.get_schema_properties())

        if form.validate_on_submit(): 
            ##TODO:  push it to notion!
            flash(f"INSERTED: {full_form.data}")

            #empty slots we don't want to reuse
            for field in full_form:
                if field.name not in ["db_url", "token", "connected"]:# and field.widget.input_type != 'hidden':
                    print(field.name)
                    field.data = ""

            return render_template('home.html', form=full_form)

        return render_template('home.html', form=full_form)

    #Just starting or bad input
    form.connected.data = False
    return render_template('home.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
