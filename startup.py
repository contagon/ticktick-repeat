from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, \
        SelectField, FileField, HiddenField, SelectMultipleField, RadioField
from wtforms.fields.html5 import IntegerField, DateField, TimeField, URLField, DecimalField, EmailField, TelField
from wtforms.validators import DataRequired, URL
from notion.client import NotionClient

import os

# connect.connected.data = False

##################################################
##########       SETTING UP FLASK       ##########
##################################################
class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class ConnectionForm(FlaskForm):
    connected = HiddenField("Connected")
    url = StringField('URL', validators=[DataRequired(), URL()])
    token = StringField('v2 Token')
    submit = SubmitField('Submit')

class RecurType(FlaskForm):
    types = SelectField('Select Recurring Type', choices=["Date with End Date", "Date with Number", "Number"], default="Dates")
    days = RadioField('Select Days', choices=["M", "W", "T"])
    start = DateField("Start Date")
    end = DateField("End Date")
    number = IntegerField("Count")

app = Flask(__name__)
app.config.from_object(Config)

##################################################
########   CONNECTING TO NOTION & FORMS   ########
##################################################
def connect_notion(url, token):
    if token == "":
        token = "blank"
    client = NotionClient(token_v2=token)
    view = client.get_collection_view(url)
    return view.collection

def make_columns(schema):
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
            options = [i['value'] for i in column['options']]
            fields[ column['slug'] ] = SelectField(column['name'], validators=[], choices=options)
        elif column['type'] == 'number':
            fields[ column['slug'] ] = DecimalField(column['name'], validators=[])
        elif column['type'] == 'checkbox':
            fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
        elif column['type'] == 'multi_select':
            options = [(i['value'], i['value']) for i in column['options']]
            fields[ column['slug'] ] = SelectMultipleField(column['name'], validators=[], choices=options)
        # elif column['type'] == 'file':
        #     fields[ column['slug'] ] = FileField(column['name'], validators=[])
        # elif column['type'] == 'relation':
        #     fields[ column['slug'] ] = BooleanField(column['name'], validators=[])

    class NotionColumns(FlaskForm):
        pass
    #apply all attributes of our temporary connect
    for k, v in fields.items():
        setattr(NotionColumns, k, v)

    return NotionColumns()

##################################################
########              PAGES               ########
##################################################
@app.route("/", methods=['GET', 'POST'])
def home():
    connect = ConnectionForm()
    recur = RecurType()

    #****************** CONNECTION FORM ******************
    if connect.validate_on_submit() and connect.connected.data == "False":
        #see if what they gave us works
        try:
            collection = connect_notion(connect.url.data, connect.token.data)
            connect.connected.data = "True"

        except Exception as e:
            #if we fail to connect, flash message and render OG connect
            flash(e)
            return render_template('home.html', connect=connect)

        #if we connected properly, give them notion connect
        columns = make_columns(collection.get_schema_properties())
        return render_template('home.html', connect=connect, recur=recur, columns=columns)


    #******************* NOTION FORM *******************
    if connect.connected.data == "True":
        #pull columns out of notion to make notion connect
        collection = connect_notion(connect.url.data, connect.token.data)
        columns = make_columns(collection.get_schema_properties())

        if connect.validate_on_submit(): 
            ##TODO:  push it to notion!
            flash(f"INSERTED: {columns.data}")

            #empty slots we don't want to reuse
            for field in columns:
                if field.name not in ["url", "token", "connected"]:# and field.widget.input_type != 'hidden':
                    print(field.name)
                    field.data = ""

            return render_template('home.html', connect=connect, recur=recur, columns=columns)

        return render_template('home.html', connect=connect, recur=recur, columns=columns)

    #Just starting or bad input
    connect.connected.data = False
    return render_template('home.html', connect=connect)

if __name__ == '__main__':
    app.run(debug=True)
