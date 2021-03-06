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


@app.route('/registerExecutive', methods=['get', 'post'])
def registerExecutive():

    if request.method == "GET":
        autodata = {}
        sid = edb.getautoSSNid()
        flash("Auto generated SSN ID : "+sid)
        autodata['ssn_id'] = sid
        return render_template('registerExecutive.html', registerExecutive=True, autodata=autodata)

    regdata = {}

    regdata['ssn_id'] = request.form.get('ssn')
    if len(regdata['ssn_id'])<9:
        flash("SSN ID length should be of minimum 9 ","danger")
        return redirect(url_for('registerExecutive'))
    if not str(regdata['ssn_id']).isdecimal():
        flash("SSN ID should only be numerical ","danger")
        return redirect(url_for('registerExecutive'))


    regdata['name'] =str( request.form.get('name')).replace("\n","")
    regdata['email'] = request.form.get('email')
    regdata['pass'] = hashlib.sha256(request.form.get('psw').encode()).hexdigest()

    if len(regdata['name'])<3:
        flash("Name Should be of minimum 3 Characters ","danger")
        return redirect(url_for('registerExecutive'))

    if not utility.isNameValid(regdata['name']):
        flash("Entered Name is invalid ","danger")
        return redirect(url_for('registerExecutive'))

    if len(regdata['email'])<1 and not '@' in regdata['email']:
        flash("Invalid Email entered ","danger")
        return redirect(url_for('registerExecutive'))

    if len(regdata['pass'])<1:
        flash("minimum length of password must be 1 character ","danger")
        return redirect(url_for('registerExecutive'))


    regdata['creation_time'] =utility.getTime()
    regdata['access_ip']=request.headers.get("x-forwarded-for",request.remote_addr)

    result, err = edb.register(regdata)

    if result:
        flash("Executive Registered Successfully ...    Login Now", "success")

        ###EMAIL SEND##
        data={}
        data['type']=utility.EMAIL_REG_EXECUTIVE
        data['ssn_id']=regdata['ssn_id']
        data['name']=regdata['name']
        data['to']=regdata['email']
        utility.sendEmail(data)
        #####
        return redirect(url_for('login'))
    else:
        flash("Failed to Register :"+err, "danger")
        return redirect(url_for('registerExecutive'))

    return redirect('login.html')


@app.route('/registerCustomer', methods=['get', 'post'])
def registerCustomer():

    if not isLoggedin():
        # if there is no one loggedIn disallow this route
        flash("Login first to access it ", "danger")
        return redirect(url_for('home'))

    if request.method == "GET":
        autodata = {}
        sid = cdb.getautoSSNid()
        flash("Auto generated SSN ID : "+sid)
        autodata['ssn_id'] = sid
        autodata['states']=utility.getState()
        return render_template('registerCustomer.html', registerCustomer=True, autodata=autodata)

    regdata = {}

    regdata['ssn_id'] = request.form.get('ssn')
    if len(regdata['ssn_id'])<9:
        flash("SSN ID length should be of minimum 9 ","danger")
        return redirect(url_for('registerCustomer'))
    if not str(regdata['ssn_id']).isdecimal():
        flash("SSN ID should only be numerical ","danger")
        return redirect(url_for('registerCustomer'))

    regdata['name'] = str(request.form.get('name')).replace("\n","").replace("  "," ")
    regdata['age'] = request.form.get('age')
    regdata['state'] = request.form.get('state')
    regdata['address'] = request.form.get('address')
    regdata['email']=request.form.get('cust_email')
    regdata['create_time']=utility.getTime()
    regdata['access_ip']=request.headers.get("x-forwarded-for",request.remote_addr)


    if len(regdata['name'])<3:
        flash("Name Should be of minimum 3 Characters ","danger")
        return redirect(url_for('registerCustomer'))
    if not utility.isNameValid(regdata['name']):
        flash("Entered Name is not Valid ","danger")
        return redirect(url_for('registerCustomer'))
    if not utility.isNameValid(regdata['address']):
        flash("Entered Address is not Valid ","danger")
        return redirect(url_for('registerCustomer'))

    if not utility.isNameValid(regdata['name']):
        flash(f"Entered Name={regdata['name']} is not Valid  ","danger")
        return redirect(url_for('registerCustomer'))

    
    if len(regdata['address'])<3:
        flash("Address Should be of minimum 3 Characters ","danger")
        return redirect(url_for('registerCustomer'))

    try:
        if int(regdata['age'])<18:
            flash("Customer should be of minimum 18 years old to Register ","danger")
            return redirect(url_for('registerCustomer'))
    except :
            flash("Customer should be of minimum 18 years old to Register ","danger")
            return redirect(url_for('registerCustomer'))

    if not utility.isStateValid(regdata['state']):
        flash("Select State from dropdown correctly ","danger")
        return redirect(url_for('registerCustomer'))
        

    result, err = cdb.registerSSN(regdata)

    if result:
        flash("Customer Registered Successfully", "success")
                ###EMAIL SEND##
        data={}
        data['type']=utility.EMAIL_REG_CUSTOMER
        data['ssn_id']=regdata['ssn_id']
        data['name']=regdata['name']
        data['to']=regdata.get('email',None)
        if data['to'] !=None:
            utility.sendEmail(data)
        else:
            logging.error(f"No valid Email found for {data['ssn_id']}")
        #####
        return redirect(url_for('viewCustomerDetail')+"/"+regdata['ssn_id'])
    else:
        flash("Failed to Register Customer "+err, "danger")

    return render_template('registerCustomer.html', registerCustomer=True)

@app.route('/logout')
def logout():
    if isLoggedin():
        # log out by invalidating session
        session_logout()
        flash("You have been successfully logged out", "success")
    else:
        flash("You are already Logged out..", "success")

    return redirect(url_for('home'))

# Utility Function

def session_logout():
    session.pop('ssn_id', None)
    session.pop('username', None)
    session.pop('last_login',None)
    # session.pop('ui',None)

def session_login(ssn_val, username,lastLogin,acc_IP,ui_type):
    session['ssn_id'] = ssn_val
    session['username'] = username
    session['last_login']=lastLogin
    session['ui']=ui_type
    access_ip=acc_IP
    edb.update_logintime(ssn_val,access_ip)

def isLoggedin():
    if 'ssn_id' in session.keys():
        return True
    else:
        return False


# Search customer by SSN ID to delete or update details
@app.route('/searchCustomer', methods=['get', 'post'])
def searchCustomer():
    if not isLoggedin():
        return redirect(url_for('login'))
    autodata = {}
    if request.method == "GET":
        if 'ssn_id' in request.args:
            autodata['ssn_id'] = request.args.get('ssn_id')
        return render_template('searchCustomer.html', searchCustomer=True, autodata=autodata)

    # make a rediection while post ..
    return redirect(url_for('updateCustomer')+"/"+request.form.get('ssn_id'))


@app.route('/updateCustomer/<ssn_id>')
@app.route('/updateCustomer', methods=['get', 'post', 'update'])
def updateCustomer(ssn_id=None):

    if not isLoggedin():
        return redirect(url_for('login'))

    if request.method == "GET":
        if ssn_id == None:
            return redirect(url_for('searchCustomer'))
        else:
            filter = {'ssn_id': ssn_id}
            # Retrieving details of customer
            result = cdb.findSSN(filter)
            if result:
                args = {}
                args['ssn_id'] = result['ssn_id']
                args['oldAge'] = result['age']
                args['oldAddress'] = result['address']
                args['oldName'] = result['name']
                args['oldState']=result['state']
                args['states']=utility.getState()
                args['oldEmail']=result.get('email',"N/A")
                return render_template('updateCustomer.html', updateCustomer=True, **args)
            else:
                flash(
                    "Unable to find customer. Try again by entering valid SSN ID.", "danger")
                return redirect(url_for('searchCustomer'))

    regdata = {}

    regdata['ssn_id'] = request.form.get('ssn_id')
    regdata['name'] = request.form.get('newName')
    regdata['age'] = request.form.get('newAge')
    regdata['address'] = request.form.get('newAddress')
    regdata['state']=request.form.get('newState')
    regdata['email']=request.form.get('newEmail')
    regdata['updated_time']=utility.getTime()
    regdata['access_ip']=request.headers.get("x-forwarded-for",request.remote_addr)

    #sanity check now

    if len(regdata['name'])<3:
        flash("Name Should be of minimum 3 Characters ","danger")
        return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])

    if not utility.isNameValid(regdata['name']):
        flash("Entered Name is not Valid ","danger")
        return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])

    
    if not utility.isNameValid(regdata['address']):
        flash("Entered Address is not Valid ","danger")
        return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])

    
    if len(regdata['address'])<3:
        flash("Address Should be of minimum 3 Characters ","danger")
        return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])

    try:
        if int(regdata['age'])<18:
            flash("Customer should be of minimum 18 years old to Register ","danger")
            return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])
    except:
            flash("Customer should be of minimum 18 years old to Register ","danger")
            return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])
            

    if not utility.isStateValid(regdata['state']):
        flash("Select State from dropdown correctly ","danger")
        return redirect(url_for('updateCustomer')+"/"+regdata['ssn_id'])


    result, err = cdb.updateSSN(regdata)

    if result:
        flash("Customer Details Updated Successfully", "success")
        return redirect(url_for('viewCustomerDetail')+"/"+regdata['ssn_id'])

    else:
        flash("Failed to Update  Customer  Details "+err, "danger")

    return redirect(url_for('searchCustomer'))


@app.errorhandler(404)
def not_found(e):
    return render_template('error404.html')