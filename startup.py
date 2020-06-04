from flask import Flask, render_template, request, make_response
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, \
        SelectField, FileField, HiddenField, SelectMultipleField, RadioField
from wtforms.fields.html5 import IntegerField, DateField, TimeField, URLField, DecimalField, EmailField, TelField
from wtforms.validators import DataRequired, URL, NumberRange, Email, Optional
from notion.client import NotionClient
from decimal import Decimal
from wtforms.compat import itervalues
from collections import OrderedDict

from datetime import datetime, timedelta

import os

class SortedForm(FlaskForm):
    def __iter__(self):
        """Iterate form fields in alphabetical order, with title first."""
        #now sort them
        fields = OrderedDict(sorted(self._fields.items(), key=lambda x: x[1].name))
        
        #find title
        title = None
        for k,v in fields.items():
            if v.id == "title":
                title = k
        #and push title to top
        if title is not None:
            fields.move_to_end(title, last=False)

        return iter(itervalues(fields))

##################################################
##########       SETTING UP FLASK       ##########
##################################################
class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

class ConnectionForm(SortedForm):
    connected = HiddenField("Connected")
    url = StringField('URL to Notion Database', validators=[DataRequired(), URL()])
    token = StringField('Notion v2 Token')
    submit = SubmitField('Submit')
    goback = SubmitField('Go Back')
    remember = BooleanField("Remember Me")

class RecurType(SortedForm):
    start_date = DateField("Start Date", validators=[Optional()])
    end_date = DateField("End Date", validators=[Optional()])
    count = IntegerField("Count", validators=[Optional()])
    # days = SelectMultipleField("Days", choices=[(i, i) for i in days])

    def validate(self):
        result = True
        if not super().validate():
            result = False

        #make sure our start and day selections are good
        if self.types.data in ["dates_mix", "dates_both"]:
            if self.start_date.data is None:
                self.start_date.errors.append("Required Field")
                result = False
            days = [self.M, self.Tu, self.W, self.Th, self.F, self.Sat, self.Sun]
            if not any([i.data for i in days]):
                self.M.errors.append("You must choose a day!")
                result = False

        #make sure our end date is good
        if self.types.data == "dates_both":
            if self.end_date.data is None:
                self.end_date.errors.append("Required Field")
                result = False
            elif self.start_date.data is not None:
                if self.start_date.data >= self.end_date.data:
                    self.end_date.errors.append("End Date is before or on Starting Date")
                    result = False

        if self.types.data == "number":
            if self.count.data < 1:
                self.count.errors.append("Enter a number greater than 0")
                result = False

        return result

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
    return client, view.collection

def make_columns(client, schema):
    #Put all columns into  a field
    dates = []
    fields = dict()
    for column in schema:
        if column['type'] == 'title' or column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[], id=column['type'])
        elif column['type'] == 'email':
            fields[ column['slug'] ] = EmailField(column['name'], validators=[Email()], id=column['type'])
        elif column['type'] == 'date':
            fields[ column['slug'] ] = DateField(column['name'], validators=[], id=column['type'])
            dates.append((column['slug'], column['name']))
        elif column['type'] == 'url':
            fields[ column['slug'] ] = URLField(column['name'], validators=[URL()], id=column['type'])
        elif column['type'] == 'person':
            persons = client.current_space.users
            options = [(i.id, i.full_name) for i in persons]
            fields[ column['slug'] ] = SelectMultipleField(column['name'], validators=[], choices=options, id=column['type'])
        elif column['type'] == 'text':
            fields[ column['slug'] ] = StringField(column['name'], validators=[], id=column['type'])
        elif column['type'] == 'phone_number':
            fields[ column['slug'] ] = TelField(column['name'], validators=[], id=column['type'])
        elif column['type'] == 'select':
            options = [("", "")] + [(i['value'], i['value']) for i in column['options']]
            fields[ column['slug'] ] = SelectField(column['name'], validators=[], choices=options, default=options[0][0], id=column['type'])
        elif column['type'] == 'number':
            fields[ column['slug'] ] = DecimalField(column['name'], validators=[], id=column['type'])
        elif column['type'] == 'checkbox':
            fields[ column['slug'] ] = BooleanField(column['name'], validators=[], id=column['type'])
        elif column['type'] == 'multi_select':
            options = [(i['value'], i['value']) for i in column['options']]
            fields[ column['slug'] ] = SelectMultipleField(column['name'], validators=[], choices=options, id=column['type'])
        # elif column['type'] == 'file':
        #     fields[ column['slug'] ] = FileField(column['name'], validators=[])
        elif column['type'] == 'relation':
            relation = client.get_collection(column['collection_id'])
            rows = relation.get_rows()
            options = [(i.id, i.title) for i in rows]
            fields[ column['slug'] ] = SelectMultipleField(column['name'], validators=[], choices=options, id=column['type'])

    #apply all attributes of our temporary form
    NotionColumns = type("NotionColumns", (SortedForm,), fields)

    #fill out the rest of our recurring form
    #includes what types to iterate over, and if there's any of them at all
    recur_params = {"date_options": SelectField("Date to Recur", choices=dates)}
    if dates == []:
        recur_params['types'] = SelectField('Select Recurring Type', choices=[("number", "Number")], default="number")
    else:
        recur_params['types'] = SelectField('Select Recurring Type', choices=[("dates_both", "Start and End Date"),
                                                        ("dates_mix", "Start Date and Number"),
                                                        ("number", "Number")], default="dates_both")
    Recur = type("RecurFull", (RecurType,), recur_params)
    
    return NotionColumns(), Recur()

##################################################
########              PAGES               ########
##################################################
@app.route("/", methods=['GET', 'POST'])
def home():
    connect = ConnectionForm()

    #******************  LOAD COOKIES  ******************
    if not connect.submit.data and "url" in request.cookies:
        connect.url.data = request.cookies["url"]
        connect.token.data = request.cookies["token_v2"]
        connect.connected.data = "True"

    #****************** GO BACK BUTTON ******************
    if connect.goback.data:
        #make it seem like we were never connected
        connect.remember.data = True
        connect.connected.data = "False"
        res = make_response( render_template('home.html', connect=connect) )
        #remove cookies to we don't accidentally reload them
        res.set_cookie("token_v2", "", max_age=0)
        res.set_cookie("url", "", max_age=0)
        return res

    #****************** CONNECTION FORM ******************
    if connect.validate_on_submit() and connect.connected.data == "False":
        #see if what they gave us works
        try:
            client, collection = connect_notion(connect.url.data, connect.token.data)
            connect.connected.data = "True"

        except:
            #if we fail to connect, flash message and render OG connect
            connect.url.errors.append("Couldn't connect to url")
            return render_template('home.html', connect=connect)

            
        #if we connected properly, give them notion form
        columns, recur = make_columns(client, collection.get_schema_properties())
        response = render_template('home.html', connect=connect, recur=recur, columns=columns)

        #if they requested to save
        if connect.remember.data:
            res = make_response(response)
            res.set_cookie("token_v2", connect.token.data, max_age=60*60*24*60)
            res.set_cookie("url", connect.url.data, max_age=60*60*24*60)
            return res
        
        return response


    #******************* NOTION FORM *******************
    if connect.connected.data == "True":
        #pull columns out of notion to make notion connect
        client, collection = connect_notion(connect.url.data, connect.token.data)
        columns, recur = make_columns(client, collection.get_schema_properties())
        
        if connect.validate_on_submit() and recur.validate_on_submit():
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
    days = ['M', 'Tu', 'W', 'Th', 'F', 'Sat', 'Sun']
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
    for k,v in params.items():
        if isinstance(v, Decimal):
            params[k] = float(v)

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
    app.run(host= '0.0.0.0', debug=True)


        
