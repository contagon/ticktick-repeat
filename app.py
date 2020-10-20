import os

from flask import Flask
from flask import make_response
from flask import render_template
from flask import request

from forms import ConnectionForm
from forms import make_tickform
from forms import RecurForm
from ticktick_utils import add_ticktick
from ticktick_utils import connect_ticktick


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
    if (
        not connect.submit.data
        and "username" in request.cookies
        and "password" in request.cookies
    ):
        connect.username.data = request.cookies["username"]
        connect.password.data = request.cookies["password"]
        connect.connected.data = "True"

    # ****************** GO BACK BUTTON ******************
    if connect.goback.data:
        # make it seem like we were never connected
        connect.remember.data = True
        connect.connected.data = "False"
        res = make_response(render_template("home.html", connect=connect))
        # remove cookies to we don't accidentally reload them
        res.set_cookie("password", "", max_age=0)
        res.set_cookie("username", "", max_age=0)
        return res

    # ****************** CONNECTION FORM ******************
    if connect.validate_on_submit() and connect.connected.data == "False":
        # see if what they gave us works
        try:
            client = connect_ticktick(connect.username.data, connect.password.data)
            connect.connected.data = "True"

        except Exception:
            # if we fail to connect, flash message and render OG connect
            connect.username.errors.append("Couldn't login")
            return render_template("home.html", connect=connect)

        # if we connected properly, give them ticktick form
        tickform = make_tickform(client)
        recur = RecurForm()
        response = render_template(
            "home.html", connect=connect, recur=recur, tickform=tickform
        )

        # if they requested to save
        if connect.remember.data:
            res = make_response(response)
            res.set_cookie("password", connect.password.data, max_age=60 * 60 * 24 * 60)
            res.set_cookie("username", connect.username.data, max_age=60 * 60 * 24 * 60)
            return res

        return response

    # *************** RECUR & ticktick FORM ***************
    if connect.connected.data == "True":
        # pull tickform out of ticktick to make ticktick connect
        client = connect_ticktick(connect.username.data, connect.password.data)
        tickform = make_tickform(client)
        recur = RecurForm()

        if (
            connect.validate_on_submit()
            and recur.validate_on_submit()
            and tickform.validate_on_submit()
        ):
            # push it to ticktick!
            add_ticktick(client, tickform.data, recur.data)

            return render_template(
                "home.html", connect=connect, recur=recur, tickform=tickform
            )

        return render_template(
            "home.html", connect=connect, recur=recur, tickform=tickform
        )

    # Just starting or bad input
    connect.connected.data = False
    return render_template("home.html", connect=connect)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
