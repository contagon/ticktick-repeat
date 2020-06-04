import os

from flask import Flask
from flask import make_response
from flask import render_template
from flask import request

from forms import ConnectionForm
from forms import make_columns
from notion_utils import add_notion
from notion_utils import connect_notion


##################################################
##########       SETTING UP FLASK       ##########
##################################################
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"


app = Flask(__name__)
app.config.from_object(Config)


##################################################
########              PAGES               ########
##################################################
@app.route("/", methods=["GET", "POST"])
def home():
    connect = ConnectionForm()

    # ******************  LOAD COOKIES  ******************
    if not connect.submit.data and "url" in request.cookies:
        connect.url.data = request.cookies["url"]
        connect.token.data = request.cookies["token_v2"]
        connect.connected.data = "True"

    # ****************** GO BACK BUTTON ******************
    if connect.goback.data:
        # make it seem like we were never connected
        connect.remember.data = True
        connect.connected.data = "False"
        res = make_response(render_template("home.html", connect=connect))
        # remove cookies to we don't accidentally reload them
        res.set_cookie("token_v2", "", max_age=0)
        res.set_cookie("url", "", max_age=0)
        return res

    # ****************** CONNECTION FORM ******************
    if connect.validate_on_submit() and connect.connected.data == "False":
        # see if what they gave us works
        try:
            client, collection = connect_notion(connect.url.data, connect.token.data)
            connect.connected.data = "True"

        except Exception:
            # if we fail to connect, flash message and render OG connect
            connect.url.errors.append("Couldn't connect to url")
            return render_template("home.html", connect=connect)

        # if we connected properly, give them notion form
        columns, recur = make_columns(client, collection.get_schema_properties())
        response = render_template(
            "home.html", connect=connect, recur=recur, columns=columns
        )

        # if they requested to save
        if connect.remember.data:
            res = make_response(response)
            res.set_cookie("token_v2", connect.token.data, max_age=60 * 60 * 24 * 60)
            res.set_cookie("url", connect.url.data, max_age=60 * 60 * 24 * 60)
            return res

        return response

    # *************** RECUR & NOTION FORM ***************
    if connect.connected.data == "True":
        # pull columns out of notion to make notion connect
        client, collection = connect_notion(connect.url.data, connect.token.data)
        columns, recur = make_columns(client, collection.get_schema_properties())

        if connect.validate_on_submit() and recur.validate_on_submit():
            # push it to notion!
            add_notion(collection, columns.data, recur.data)

            return render_template(
                "home.html", connect=connect, recur=recur, columns=columns
            )

        return render_template(
            "home.html", connect=connect, recur=recur, columns=columns
        )

    # Just starting or bad input
    connect.connected.data = False
    return render_template("home.html", connect=connect)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
