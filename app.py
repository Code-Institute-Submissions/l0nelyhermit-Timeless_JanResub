from flask import Flask, render_template,request,redirect,url_for, flash
import flask_login
import os
import pymongo
from dotenv import load_dotenv
from bson.objectid import ObjectId
from passlib.hash import pbkdf2_sha256
import datetime
import random

# Load Environment Variables
load_dotenv()

app= Flask(__name__)

# Setting up the secret key to the Flask app
app.secret_key = os.environ.get('SECRET_KEY')

MONGO_URI= os.environ.get('MONGO_URI')
DB_NAME = "Timeless"

# Connect to the MongoDB Database
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

class User(flask_login.UserMixin):
    pass

# Initialise the flask-login for the Flask App
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
# login_manager.login_view = 'login_user'
login_manager.refresh_view = 'login_user'
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)


@login_manager.user_loader
def user_loader(email):
    user = db.Users.find_one({
        'Email':email
    })
    # If user exists in the database
    if user:
        user_object = User()
        user_object.id = user["Email"]
        return user_object
    else:
        # If the user is not found in the database, raise an error
        return None



# Security Questions For Registering User
all_security_questions = [
    'What was the name of your second pet?',
    'Who was your childhood hero?',
    'What was your childhood nickname?',
    'In what city or town was your first job?',
    'What was the name of your first stuffed animal'
]

# Welcome Page of the Website
@app.route('/')
def welcome_user():
    return render_template('welcome_user.template.html')

# Account creation system (Process Registration)
@app.route('/register',methods=['GET','POST'])
def register_user():
    # Retrieves the Form for the User to  Register
    if request.method =="GET":
        return render_template('register_user.template.html', questions=all_security_questions, errors={})
    else:
    # Retrieve the information from the registration form
        fname = request.form.get('name')
        email = request.form.get('email')
        dob = request.form.get('dob')
        country = request.form.get('country')
        username = request.form.get('username')
        password = request.form.get('password')
        securityquestion = request.form.get('SecurityQuestion')
        securityanswer = request.form.get('SecurityAnswer')
    
    # Form Field Validation
        # Error Accumulator Collector
        errors = {}
        
        database_error = False
        # Check if Full Name entered is valid
        if len(fname) <3 or len(fname)>70:
            flash('Error: Invalid Name', 'danger')
            errors.update(invalid_name="Please key in a valid name")
    # Database Validation
        # Check if the User already exists in the database
        elif database_error == False:
            username_check = db.Users.find_one({
            'Username': username
            })
            # Check if user entered an email that exists in database
            email_check = db.Users.find_one({
                'Email': email
            })
            # SCENARIOS:
            # 1. If user enters same username as another exisitng user, raise error
            # 2. If user enters same email as another existing user, raise error
            # 3. If user enters same username and same email as another existing user, raise error
            # 4. If user does not exist, proceed with creation

            # if username does not match with any existing in database
            if not username_check:
                if email_check:
                    # If user enters same email as another existing user, raise error
                    if email == email_check['Email']:
                        flash('Error: Email has already been used, please try again with another valid email','danger')
                        errors.update(invalid_email="Email has already been used, please enter a valid email")
                        database_error = True
                else:
                    if len(errors) > 0:
                        flash("Registration Failure",'danger')
                        return render_template('register_user.template.html',questions=all_security_questions,
                                                    errors=errors)
                    else:
                        #  No errors in registration, proceed with registration
                        # Create a new account and new profile for the user
                    
                        # Instance Variable for the Maximum Number Of Users for the site
                        max_capacity_users = 9999
                        # Issues a random ID number for the account ID
                        number = random.randint(0, max_capacity_users)

                        # Issues a random ID number for the profile ID
                        profileID = random.randint(0,max_capacity_users)

                        new_user = {
                            'AccountID': number,
                            'Full_Name': fname,
                            'Email': email,
                            'Date_Of_Birth': datetime.datetime.strptime(dob, "%Y-%m-%d"),
                            'Country': country,
                            'Username': username,
                            'Password': pbkdf2_sha256.hash(password),
                            'SecurityQuestion': securityquestion,
                            'SecurityAnswer': securityanswer
                        }

                        # Using Flags Technique, if account can be successfully created, proceed with profile creation

                        create_account_success = False
                        try:
                            db.Users.insert_one(new_user)
                            create_account_success = True
                        except Exception as e:
                            return str(e)

                        if create_account_success == True:
                            # extra variables for profile
                            bio = ''
                            datejoined = datetime.datetime.now()
                            new_profile = {
                                'ProfileID':profileID,
                                'AccountID': new_user,
                                'Full_Name': fname,
                                'Email': email,
                                'Date_Of_Birth': datetime.datetime.strptime(dob, "%Y-%m-%d"),
                                'Country': country,
                                'Username': username,
                                'Bio': bio,
                                'Date_Joined': datejoined
                            }

                            db.Profiles.insert_one(new_profile)

                            flash("Your Account has been created", "success")
                            user_logged_in = User()
                            user_email = db.Users.find_one({
                                'Email':email
                            })
                            user_logged_in.id = user_email['Email']
                            flask_login.login_user(user_logged_in)

                            return redirect(url_for('home'))

            else:
                 #  If user enters username that matches another existing username, raise error
                if username == username_check['Username']:
                    flash('Error: account already exists, please try again with another valid username','danger')
                    errors.update(invalid_username="Account already exists,please proceed to login")
                    database_error = True
                    # if user enters username and email that matches another existing username and email, raise error
                    if email_check:
                        if email_check['Email'] ==email and username_check['Username']==username:
                            flash('Error: Email and Username have been used already,please enter something different','danger')
                            errors.update(invalid_email_and_username="Email and Username have been used, please try something different")
                            database_error = True
           

            if len(errors) > 0:
                        flash("Registration Failure",'danger')
                        return render_template('register_user.template.html',questions=all_security_questions,
                                                    errors=errors)

    



@app.route('/login', methods=['GET','POST'])
def login_user():
    # Retrieves the login webpage for the user to login
    if request.method =="GET":
        return render_template('login_user.template.html',errors={})
    else:
    # Retrieve the information from the login form
        email = request.form.get('email')
        password = request.form.get('password')
    
    # Login Validation
        # Accumulator
        # Check if the user email exists in the database
        check_user = db.Users.find_one({
            'Email':email
        })
        # If the user exists and the password matches,authorize the user
        if check_user and pbkdf2_sha256.verify(password,check_user['Password']):
            user_logged_in = User()
            user_logged_in.id = check_user['Email']
            flask_login.login_user(user_logged_in)

            flash('Login successful','success')
            return redirect(url_for('home'))
        # If the user does not exist, raise error
        elif not check_user:
            flash('Invalid Login, no account exists','danger')
            return render_template('login_user.template.html')
        # If the login failed due to incorrect input, raise error
        else:
            flash('Wrong Email or Password','danger')
            return render_template('login_user.template.html')


# Logout Functionality
@app.route('/logout')
def logout():
    flask_login.logout_user()
    flash('Logged Out','success')
    return redirect(url_for('login_user'))

# Main Web Application After Login
@app.route('/home')
@flask_login.login_required
def home():
    return render_template('home.template.html')


# Editing User Account Information
@app.route('/edit/account/',methods=['GET','POST'])
@flask_login.login_required
def edit_user_account():
    # Retrieves the edit account page for the user to edit account particulars
    if request.method =="GET":
        current_user = db.Users.find_one({
            'Email':flask_login.current_user.get_id()
        })
        return render_template('update_account.template.html',current_user=current_user,questions=all_security_questions)
    else:
        # Retrieve the updated fields information
        fname = request.form.get('name')
        email = request.form.get('email')
        dob = request.form.get('dob')
        country = request.form.get('country')
        username = request.form.get('username')
        password = request.form.get('password')
        securityquestion = request.form.get('SecurityQuestion')
        securityanswer = request.form.get('SecurityAnswer')
    

        # Form Field Validation
        # Error Accumulator Collector
        errors = {}
        
        database_error = False
        # Check if Full Name entered is valid
        if len(fname) <3 or len(fname)>70:
            flash('Error: Invalid Name', 'danger')
            errors.update(invalid_name="Please key in a valid name")
        
        # Database Validation
        elif database_error == False:
            # Check if the User already exists in the database
            username_check = db.Users.find_one({
            'Username': username
            })
            # Check if user entered an email that exists in database
            email_check = db.Users.find_one({
                'Email': email
            })
            # SCENARIOS:
            # Check against database for existing information that is the same with other users
            # 1. User wishes to keep email, change username
            # 2. User wishes to keep username , change email
            if not username_check:
                if email_check:
                    # If user enters same email as another existing user, raise error
                    if email == email_check['Email']:
                        flash('Error: Email has already been used, please try again with another valid email','danger')
                        errors.update(invalid_email="Email has already been used, please enter a valid email")
                        database_error = True
                else:
                    # Check if errors occurred, if there are errors, display failure message
                    if len(errors) > 0:
                        flash("Update Failure",'danger')
                        return redirect(url_for('edit_user_account'))
                    else:

                        db.Profiles.update({
                            'Email': flask_login.current_user.get_id()
                        }, {
                            '$set': {
                                'Full_Name': fname,
                                'Email': email,
                                'Date_Of_Birth': datetime.datetime.strptime(dob, "%Y-%m-%d"),
                                'Country': country,
                                'Username': username,
                            }
                        })

                        db.Users.update({
                            'Email': flask_login.current_user.get_id()
                        }, {
                            '$set': {
                                    'Full_Name': fname,
                                    'Email': email,
                                    'Date_Of_Birth': datetime.datetime.strptime(dob, "%Y-%m-%d"),
                                    'Country': country,
                                    'Username': username,
                                    'Password': pbkdf2_sha256.hash(password),
                                    'SecurityQuestion': securityquestion,
                                    'SecurityAnswer': securityanswer
                            }
                        })

                        flash("Your Account has been updated successfully,Please Login Again","success")

                        return redirect(url_for('welcome_user'))
            else:
                 #  If user enters username that matches another existing username, raise error
                if username == username_check['Username']:
                    flash('Error: account already exists, please try again with another valid username','danger')
                    errors.update(invalid_username="Account already exists,please proceed to login")
                    database_error = True
                    # if user enters username and email that matches another existing username and email, raise error
                    if email_check:
                        if email_check['Email'] ==email and username_check['Username']==username:
                            flash('Error: Email and Username have been used already,please enter something different','danger')
                            errors.update(invalid_email_and_username="Email and Username have been used, please try something different")
                            database_error = True

            if len(errors) > 0:
                        flash("Update Failure",'danger')
                        return redirect(url_for('edit_user_account'))



# Delete Account from Database
@app.route('/delete/account/',methods=['GET','POST'])
@flask_login.login_required
def delete_user_account():
    # Retrieve the information of the user from the database
    if request.method =="GET":
        current_user = db.Users.find_one({
            'Email':flask_login.current_user.get_id()
        })
        return render_template('delete_account.template.html',current_user=current_user)
    else:
        # Remove both profile and account from the database
        db.Profiles.remove({
            'Email':flask_login.current_user.get_id()
        })
        db.Users.remove({
            'Email':flask_login.current_user.get_id()
        })
        flash("Your Account has been deleted successfully","success")
        return redirect(url_for('welcome_user'))




if __name__ == "__main__":
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)