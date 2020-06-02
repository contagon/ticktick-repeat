from flask import Flask, render_template, flash, redirect, url_for, request, session
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, \
        SelectField, FileField, HiddenField, SelectMultipleField, RadioField
from wtforms.fields.html5 import IntegerField, DateField, TimeField, URLField, DecimalField, EmailField, TelField
from wtforms.validators import DataRequired, URL, NumberRange, Email
from notion.client import NotionClient

from datetime import datetime, timedelta

import os

# connect.connected.data = False

##################################################
##########       SETTING UP FLASK       ##########
##################################################
class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class ConnectionForm(FlaskForm):
    connected = HiddenField("Connected")
    url = StringField('URL', validators=[DataRequired(), URL()], render_kw={"placeholder": "URL to Notion Database"})
    token = StringField('v2 Token', render_kw={"placeholder": "Notion v2 Token"})
    submit = SubmitField('Submit')

class RecurType(FlaskForm):
    types = SelectField('Select Recurring Type', choices=[("dates_both", "Start and End Date"),
                                                        ("dates_mix", "Start Date and Number"),
                                                        ("number", "Number")], default="dates_both")
    start_date = DateField("Start Date", default=datetime.now())
    end_date = DateField("End Date", default=datetime.now()+timedelta(days=1))
    count = IntegerField("Count", default=1, validators=[NumberRange(min=1)])

days = ['M', 'Tu', 'W', 'Th', 'F', 'Sat', 'Sun']
for day in days:
    setattr(RecurType, day, BooleanField(day))

app = Flask(__name__)
app.config.from_object(Config)

##################################################
########   CONNECTING TO NOTION & FORMS   ########
##################################################
def connect_notion(url, token):
    if token == "":
        token = os.environ.get('BOT_TOKEN')
    client = NotionClient(token_v2=token)
    view = client.get_collection_view(url)
    return view.collection

def make_columns(schema):
    #Put all columns into  a field
    dates = []
    fields = dict()
    for column in schema:
        if column['type'] == 'title' or column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[])
        elif column['type'] == 'email':
            fields[ column['slug'] ] = EmailField(column['name'], validators=[Email()])
        elif column['type'] == 'date':
            fields[ column['slug'] ] = DateField(column['name'], validators=[])
            dates.append((column['slug'], column['name']))
        elif column['type'] == 'url':
            fields[ column['slug'] ] = URLField(column['name'], validators=[])
        # elif column['type'] == 'person':
        #     fields[ column['slug'] ] = BooleanField(column['name'], validators=[])
        elif column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[])
        elif column['type'] == 'phone_number':
            fields[ column['slug'] ] = TelField(column['name'], validators=[])
        elif column['type'] == 'select':
            options = [("", "")] + [(i['value'], i['value']) for i in column['options']]
            fields[ column['slug'] ] = SelectField(column['name'], validators=[], choices=options, default=options[0][0])
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

    if dates == []:
        dates.append("NO DATES TO RECUR ON")
    Recur = type("RecurFull", (RecurType,), {"date_options": SelectField("Date to Recur", choices=dates)})
    return NotionColumns(), Recur()

##################################################
########              PAGES               ########
##################################################
@app.route("/", methods=['GET', 'POST'])
def home():
    connect = ConnectionForm()

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
        columns, recur = make_columns(collection.get_schema_properties())
        return render_template('home.html', connect=connect, recur=recur, columns=columns)


    #******************* NOTION FORM *******************
    if connect.connected.data == "True":
        #pull columns out of notion to make notion connect
        collection = connect_notion(connect.url.data, connect.token.data)
        columns, recur = make_columns(collection.get_schema_properties())

        if connect.validate_on_submit(): 
            #push it to notion!
            add_notion(collection, columns.data, recur.data)

            return render_template('home.html', connect=connect, recur=recur, columns=columns)

        return render_template('home.html', connect=connect, recur=recur, columns=columns)

    #Just starting or bad input
    connect.connected.data = False
    return render_template('home.html', connect=connect)

#################################################
########        ADDING TO NOTION         ########
#################################################

def add_notion(collection, params, recur):
    #parse through recur data
    start_date = recur["start_date"]
    end_date = recur["end_date"]
    count = recur["count"]
    types = recur["types"]
    date_options = recur["date_options"]
    days = []
    if recur["M"]:
        days.append(0)
    if recur["Tu"]:
        days.append(1)
    if recur["W"]:
        days.append(2)
    if recur["Th"]:
        days.append(3)
    if recur["F"]:
        days.append(4)
    if recur["Sat"]:
        days.append(5)
    if recur["Sun"]:
        days.append(6)

    #clean out params given
    params.pop('csrf_token')

    # Set up iterative variables
    if types in ["dates_both", "dates_mix"]:
        params[date_options] = start_date
    if types in ["dates_mix", "number"]:
        ccount = 0

    still_going = True
    while still_going:
        #if that's not a day we're supposed to add, skip (and check if we should stop)
        if types in ["dates_both", "dates_mix"] and params[date_options].weekday() not in days:
            params[date_options] += timedelta(days=1)
            if types == "dates_both" and params[date_options] > end_date:
                still_going = False
            continue

        #add it
        collection.add_row(**params)

        #increment date and count (and check if we should stop)
        if types in ["dates_both", "dates_mix"]:
            params[date_options] += timedelta(days=1)
        if types == "dates_both" and params[date_options] > end_date:
            still_going = False
        if types in ["dates_mix", "number"]:
            ccount += 1
            if ccount >= count:
                still_going = False

if __name__ == '__main__':
    app.run(debug=True)


        
