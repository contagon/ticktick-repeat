from collections import OrderedDict

from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import HiddenField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.compat import itervalues
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import DecimalField
from wtforms.fields.html5 import EmailField
from wtforms.fields.html5 import IntegerField
from wtforms.fields.html5 import TelField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import Optional
from wtforms.validators import URL


# This is used to iterate through columns how we want
class SortedForm(FlaskForm):
    def __iter__(self):
        """Iterate form fields in alphabetical order, with title first."""
        # now sort them
        fields = OrderedDict(sorted(self._fields.items(), key=lambda x: x[1].name))

        # find title
        title = None
        for k, v in fields.items():
            if v.id == "title":
                title = k
        # and push title to top
        if title is not None:
            fields.move_to_end(title, last=False)

        return iter(itervalues(fields))


# used for connection page
class ConnectionForm(FlaskForm):
    connected = HiddenField("Connected")
    url = StringField("URL to Notion Database", validators=[DataRequired(), URL()])
    token = StringField("Notion v2 Token")
    submit = SubmitField("Submit")
    goback = SubmitField("Go Back")
    remember = BooleanField("Remember Me")


# Used for recurring settings. To validate different types of recurring
# we had to make our own validation
class RecurType(FlaskForm):
    start_date = DateField("Start Date", validators=[Optional()])
    end_date = DateField("End Date", validators=[Optional()])
    count = IntegerField("Count", validators=[Optional()])

    def validate(self):
        result = True
        if not super().validate():
            result = False

        # make sure our start and day selections are good
        if self.types.data in ["dates_mix", "dates_both"]:
            if self.start_date.data is None:
                self.start_date.errors.append("Required Field")
                result = False
            days = [self.M, self.Tu, self.W, self.Th, self.F, self.Sat, self.Sun]
            if not any([i.data for i in days]):
                self.M.errors.append("You must choose a day!")
                result = False

        # make sure our end date is good
        if self.types.data == "dates_both":
            if self.end_date.data is None:
                self.end_date.errors.append("Required Field")
                result = False
            elif self.start_date.data is not None:
                if self.start_date.data >= self.end_date.data:
                    self.end_date.errors.append(
                        "End Date is before or on Starting Date"
                    )
                    result = False

        if self.types.data == "number":
            if self.count.data < 1:
                self.count.errors.append("Enter a number greater than 0")
                result = False

        return result


# lazily add day checkboxes
days = ["M", "Tu", "W", "Th", "F", "Sat", "Sun"]
for day in days:
    setattr(RecurType, day, BooleanField(day))


# Used to pull notion columns and make form from them
# Also used to finish making recur form
def make_columns(client, schema):
    # Put all columns into  a field
    dates = []
    fields = dict()
    for column in schema:
        if column["type"] == "title" or column["type"] == "text":
            fields[column["slug"]] = StringField(
                column["name"], validators=[], id=column["type"]
            )
        elif column["type"] == "email":
            fields[column["slug"]] = EmailField(
                column["name"], validators=[Email()], id=column["type"]
            )
        elif column["type"] == "date":
            fields[column["slug"]] = DateField(
                column["name"], validators=[], id=column["type"]
            )
            dates.append((column["slug"], column["name"]))
        elif column["type"] == "url":
            fields[column["slug"]] = URLField(
                column["name"], validators=[URL()], id=column["type"]
            )
        elif column["type"] == "person":
            persons = client.current_space.users
            options = [(i.id, i.full_name) for i in persons]
            fields[column["slug"]] = SelectMultipleField(
                column["name"], validators=[], choices=options, id=column["type"]
            )
        elif column["type"] == "text":
            fields[column["slug"]] = StringField(
                column["name"], validators=[], id=column["type"]
            )
        elif column["type"] == "phone_number":
            fields[column["slug"]] = TelField(
                column["name"], validators=[], id=column["type"]
            )
        elif column["type"] == "select":
            options = [("", "")] + [(i["value"], i["value"]) for i in column["options"]]
            fields[column["slug"]] = SelectField(
                column["name"],
                validators=[],
                choices=options,
                default=options[0][0],
                id=column["type"],
            )
        elif column["type"] == "number":
            fields[column["slug"]] = DecimalField(
                column["name"], validators=[], id=column["type"]
            )
        elif column["type"] == "checkbox":
            fields[column["slug"]] = BooleanField(
                column["name"], validators=[], id=column["type"]
            )
        elif column["type"] == "multi_select":
            options = [(i["value"], i["value"]) for i in column["options"]]
            fields[column["slug"]] = SelectMultipleField(
                column["name"], validators=[], choices=options, id=column["type"]
            )
        # elif column['type'] == 'file':
        #     fields[ column['slug'] ] = FileField(column['name'], validators=[])
        elif column["type"] == "relation":
            relation = client.get_collection(column["collection_id"])
            rows = relation.get_rows()
            options = [(i.id, i.title) for i in rows]
            fields[column["slug"]] = SelectMultipleField(
                column["name"], validators=[], choices=options, id=column["type"]
            )

    # apply all attributes of our temporary form
    NotionColumns = type("NotionColumns", (SortedForm,), fields)

    # fill out the rest of our recurring form
    # includes what types to iterate over, and if there's any days to iterate through
    recur_params = {"date_options": SelectField("Date to Recur", choices=dates)}
    if dates == []:
        recur_params["types"] = SelectField(
            "Select Recurring Type", choices=[("number", "Number")], default="number"
        )
    else:
        recur_params["types"] = SelectField(
            "Select Recurring Type",
            choices=[
                ("dates_both", "Start and End Date"),
                ("dates_mix", "Start Date and Number"),
                ("number", "Number"),
            ],
            default="dates_both",
        )
    Recur = type("RecurFull", (RecurType,), recur_params)

    return NotionColumns(), Recur()
