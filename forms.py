from collections import OrderedDict

from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import FormField
from wtforms import HiddenField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import IntegerField
from wtforms.fields.html5 import TimeField
from wtforms.validators import DataRequired
from wtforms.validators import Optional
from wtforms.widgets import PasswordInput
from wtforms_components import SelectField as GroupedSelectField


# used to give optional time along with dates
class MyDateTime(FlaskForm):
    date = DateField("Date", validators=[Optional()])
    time = TimeField("Time", validators=[Optional()])

    def validate(self):
        result = True
        if not super().validate():
            result = False
        if not self.date.data and self.time.data:
            self.date.errors.append("You can't submit only a time")
            result = False
        return result


# used for connection page
class ConnectionForm(FlaskForm):
    connected = HiddenField("Connected")
    username = StringField("Username", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()], widget=PasswordInput(hide_value=False))
    submit = SubmitField("Submit")
    goback = SubmitField("Go Back")
    remember = BooleanField("Remember Me")


# Used for recurring settings. To validate different types of recurring
# we had to make our own validation
class RecurForm(FlaskForm):
    start_date = FormField(MyDateTime, label="Start Date")
    end_date = FormField(MyDateTime, label="End Date")
    count = IntegerField("Count", validators=[Optional()])
    timezone = HiddenField("Timezone")

    types = SelectField(
        "Recur Type",
        choices=[
            ("dates_both", "Start and End Date"),
            ("dates_mix", "Start Date and Number"),
            ("number", "Number"),
        ],
        default="dates_both",
    )

    def validate(self):
        result = True
        if not super().validate():
            result = False

        # make sure starting date is good to go
        if self.types.data in ["dates_mix", "dates_both"]:
            # make sure there's a starting date
            if self.start_date.date.data is None:
                self.start_date.date.errors.append("Required Field")
                result = False

            # make sure they chose a day
            days = [self.M, self.Tu, self.W, self.Th, self.F, self.Sat, self.Sun]
            if not any([i.data for i in days]):
                self.M.errors.append("You must choose a day!")
                result = False

        # make sure our end date is good
        if self.types.data == "dates_both":
            # make sure there is one
            if self.end_date.date.data is None:
                self.end_date.date.errors.append("Required Field")
                result = False
            # make sure it's after the starting date
            elif self.start_date.date.data is not None:
                if self.start_date.date.data >= self.end_date.date.data:
                    self.start_date.date.errors.append(
                        "End Date is before or on Starting Date"
                    )
                    result = False

        if self.types.data == "number":
            if not self.count.data:
                self.count.errors.append("A Number is Required")
                result = False
            elif self.count.data < 1:
                self.count.errors.append("Enter a number greater than 0")
                result = False

        return result


# lazily add day checkboxes
days = ["M", "Tu", "W", "Th", "F", "Sat", "Sun"]
for day in days:
    setattr(RecurForm, day, BooleanField(day, id="single_day"))


# Used to pull ticktick tickform and make form from them
# Also used to finish making recur form
def make_tickform(client):
    # Put all tickform into  a field
    fields = dict()
    fields['title'] = StringField("Title", validators=[Optional()])

    # Lists
    groups = {item['id']: [item['name']] for item in client.list_groups}
    others = []
    for item in client.lists:
        if item['closed'] != True:
            try:
                groups[item['groupId']].append( (item['name'], item['name']) )
            except:
                others.append( (item['name'], item['name']) )
    options = [("", "Inbox")] + others + [(i[0], i[1:]) for i in groups.values()]
    fields['list'] = GroupedSelectField("List", choices=options, validators=[Optional()])

    # Due Date
    fields['dueDate'] = FormField(MyDateTime, label="Due Date")

    # Tags
    options = [(i['name'], i['label']) for i in client.tags]
    fields['tags'] = SelectMultipleField("Tags", choices=options, validators=[Optional()])

    fields['priority'] = SelectField("Priority", choices=[(0, "None"), (1, "Low"), (3, "Medium"), (5, "High")], validators=[Optional()])

    # apply all attributes of our temporary form
    TickForm = type("TickForm", (FlaskForm,), fields)

    return TickForm()
