from retail_banking import *
from . import utility
from time import gmtime, strftime
import time
import logging
from flask import redirect, render_template, url_for, json, flash


@app.route('/')
def home():
    return render_template('home.html', home=True)

@app.route('/ui')
def UI():
    try:
        ui_type=int(request.args.get('ui',1))
        session_ui(ui_type)
    except :
        pass
    return redirect(url_for('home'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if isLoggedin():
        # redirect in case user is already logged In
        return(redirect(url_for('home')))
    if request.method == "GET":
        # show when default this url is loaded ..
        return render_template('login.html', login=True)
    else:
        # after user submit his username and password we get to this...
        uid = request.form.get('uid', "userNotFound")
        password = request.form.get('psw', "passwordNotfound")
        passhax = hashlib.sha256(password.encode()).hexdigest()

        filter = {'ssn_id': uid, 'pass': passhax}

        result = edb.find(filter)

        if result == None:
            flash("Wrong UserName or Password retry", "danger")
            return redirect(url_for('login'))
        else:
            # setup session~~~
            last_login=result.get("last_login","N/A")
            ui_type=result.get('ui','base1.html')
            session_login(uid, result['name'],last_login,request.headers.get("x-forwarded-for",request.remote_addr),ui_type)
            if isLoggedin():

                flash("Successfully Logged in", "success")
            else:
                flash("Can not setup session ", "danger")
            # end setup

            return redirect(url_for('home'))