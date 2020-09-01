from flask import Flask, render_template,request,redirect,url_for, flash
import flask_login
import os
import pymongo
from dotenv import load_dotenv
from bson.objectid import ObjectId
from passlib.hash import pbkdf2_sha256
import datetime
import random
from bs4 import BeautifulSoup
from country_list import countries_for_language
import json
import math



# Load Environment Variables
load_dotenv()

# Cloundinary Variables
CLOUD_NAME = os.environ.get('CLOUD_NAME')
UPLOAD_PRESET=os.environ.get('UPLOAD_PRESET')

app= Flask(__name__, static_url_path='/static')

# Setting up the secret key to the Flask app
app.secret_key = os.environ.get('SECRET_KEY')

MONGO_URI= os.environ.get('MONGO_URI')
DB_NAME = "Timeless"


# Connect to the MongoDB Database
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

 # Instance Variable for the Maximum Number Of Users,Posts and Listings for the site
max_capacity_users = 9999



class User(flask_login.UserMixin):
    pass

# Initialise the flask-login for the Flask App
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_user'
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
        user_object.username = user["Username"]
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


countries = dict(countries_for_language('en'))
country_list = countries.values()
# Account creation system (Process Registration)
@app.route('/register',methods=['GET','POST'])
def register_user():
    if request.method =="GET":
        return render_template('register_user.template.html', questions=all_security_questions, errors={},countries=country_list)
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

                        if len(errors) > 0:
                            flash("Registration Failure",'danger')
                            return render_template('register_user.template.html',questions=all_security_questions,
                                                errors=errors)
                else:
                    if len(errors) > 0:
                        flash("Registration Failure",'danger')
                        return render_template('register_user.template.html',questions=all_security_questions,
                                                errors=errors)
                    else:
                        # No errors in registration, proceed with registration
                        # Create a new account and new profile for the user
                        # Issues a random ID number for the account ID that is unique and not repeated
                        account_number_list = list(range(1,max_capacity_users))
                        random.shuffle(account_number_list)
                        number = account_number_list.pop()
                        # Issues a random ID number for the profile ID that is unique and not repeated
                        profile_number_list = list(range(1,max_capacity_users))
                        random.shuffle(profile_number_list)
                        profileID = profile_number_list.pop()

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
                            user_data = db.Users.find_one({
                                'Email':email
                            })
                            user_logged_in.id = user_data['Email']
                            user_logged_in.username = user_data['Username']
                            flask_login.login_user(user_logged_in)
                            return redirect(url_for('home'))
            else:
                if username_check['Username'] ==username:
                    #  If user enters username that matches another existing username, raise error
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

        



@app.route('/', methods=['POST'])
def login_user():
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
            user_logged_in.username = check_user['Username']
            flask_login.login_user(user_logged_in)

            flash('Login successful','success')
            return redirect(url_for('home'))
        # If the user does not exist, raise error
        elif not check_user:
            flash('Invalid Login, no account exists','danger')
            return redirect(url_for('welcome_user'))
        # If the login failed due to incorrect input, raise error
        else:
            flash('Wrong Email or Password','danger')
            return redirect(url_for('welcome_user'))


# Logout Functionality
@app.route('/logout')
def logout():
    flask_login.logout_user()
    flash('Logged Out','success')
    return redirect(url_for('welcome_user'))

# Main Web Application After Login
@app.route('/home')
def home():
    posts = db.Posts.find()
    return render_template('home.template.html',posts=posts)


# Editing User Account Information
@app.route('/edit/account/',methods=['GET','POST'])
@flask_login.login_required
def edit_user_account():
    # Retrieves the edit account page for the user to edit account particulars
    if request.method =="GET":
        current_user_logged_in = db.Users.find_one({
            'Email':flask_login.current_user.get_id()
        })
        return render_template('update_account.template.html',current_user_logged_in=current_user_logged_in,questions=all_security_questions)
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

# Go To Profile Page of the User
@app.route('/profile',methods=['GET'])
@flask_login.login_required
def show_user_profile():
    current_profile = db.Profiles.find_one({
        'Email':flask_login.current_user.get_id()
    })
    return render_template('show_profile.template.html',current_profile=current_profile)


# Allowing User to Edit Profile
@app.route('/edit/profile',methods=['GET','POST'])
@flask_login.login_required
def edit_user_profile():
    if request.method == 'GET':
        # Retrieving the information of the user profile from the database
        current_profile = db.Profiles.find_one({
            'Email': flask_login.current_user.get_id()
        })
        return render_template('update_profile.template.html',current_profile=current_profile)
    else:
        # Retrieve the updated fields information
        bio = request.form.get('bio')
        fname = request.form.get('name')
        country = request.form.get('country')

        # Field Validation
        # Error Accumulator
        errors={}

        # Check if input name is valid
        if len(fname) <3 or len(fname)>70:
            flash('Error: Invalid Name', 'danger')
            errors.update(invalid_name="Please key in a valid name")
            # If errors discovered, raise error and redirect to edit user profile form
            if len(errors) > 0:
                flash("Update Failure",'danger')
                return redirect(url_for('edit_user_profile'))
        else:
            db.Profiles.update({
                'Email': flask_login.current_user.get_id()
                }, {
                    '$set': {
                        'Full_Name': fname,
                        'Bio': bio,
                        'Country': country,
                            }
                        })
            
            flash("Your Profile has been updated successfully","success")
            return redirect(url_for('show_user_profile'))


# Creation of the Post System, Delete My Posts, Edit My Posts, See My Posts
@app.route('/create/post',methods=['GET','POST'])
@flask_login.login_required
def create_post():
    if request.method =="GET":
        # Loads the create post form for the user
        return render_template('create_post.template.html',errors={})
    else: 
        # Retrieve the information from the fields of the form
        title = request.form.get('title')
        content = request.form.get('editordata')

        # Validate the form inputs
        # Accumulator
        errors = {}
        # Check if title is empty
        if title == "":
            flash('Error: Invalid Title','danger')
            errors.update(invalid_title="Title Field is Empty, please enter a valid title")
        # Check if content is empty
        elif content =="":
            flash("Error: Invalid Content",'danger')
            errors.update(invalid_content="Content Field is Empty,please enter a valid content")
        # If errors, redirect back to the create post page and raise error
        if len(errors) > 0:
            flash("Create Failure",'danger')
            return redirect(url_for('create_post'))
        # If no errors, insert post data into database
        else:
            # Issues a random ID number for the profile ID that is unique and not repeated
            post_number_list = list(range(1,max_capacity_users))
            random.shuffle(post_number_list)
            postID = post_number_list.pop()
            dateposted = datetime.datetime.now()
            votes=int()
            comments = []
            content_soup = BeautifulSoup(content,"html.parser")

            new_post = {
                'PostID':postID,
                'Title':title,
                'Content':content_soup.get_text(),
                'Votes': votes,
                'Comments': comments,
                'Date_Posted':dateposted,
                'Username': flask_login.current_user.username
            }

            db.Posts.insert_one(new_post)
            flash("Your Post has been created", "success")
            return redirect(url_for('home'))

    
# Allow User to See the Posts that the User has made
# My Posts Section
@app.route('/myposts',methods=['GET'])
@flask_login.login_required
def show_user_posts():
    
    # Get Total number of results based on database
    number_of_results = db.Posts.find({
        'Username':flask_login.current_user.username
    }).count()
    page_size = 2
    number_of_pages = math.ceil(number_of_results/page_size)-1
    # Get the current page number from the args get request, if it does not exist set it to zero
    page_number = request.args.get('page_number') or '0'
    page_number = int(page_number)
    # calculate how many results will be skipped depending on page number
    number_to_skip = page_number * page_size

    user_posts = db.Posts.find({
        'Username':flask_login.current_user.username
    }).skip(number_to_skip).limit(page_size)

    return render_template('user_posts.template.html',user_posts=user_posts,
                        page_number=page_number,number_of_pages=number_of_pages)

# Allow Users to click on each post to view the full content 
@app.route('/post/<post_id>',methods=['GET','POST'])
@flask_login.login_required
def show_post(post_id):
    if request.method =="GET":
        # Get Total number of results based on database
        cursor = db.Posts.aggregate([
            {
                '$match':{'_id':ObjectId(post_id)}
            },
            {
                '$project':{
                    'count':{'$size':'$Comments'}
                }
            }
        ])
        results = list(cursor)
        for i in results:
                comment_data=i
        number_of_comment = comment_data['count']
        page_size = 3
        number_of_pages = math.ceil(number_of_comment/page_size)-1
        # Get the current page number from the args get request, if it does not exist set it to zero
        page_number = request.args.get('page_number') or '0'
        page_number = int(page_number)
        # calculate how many results will be skipped depending on page number
        number_to_skip = page_number * page_size

        post = db.Posts.find_one({
             '_id':ObjectId(post_id)
            },{'Comments':{'$slice':[number_to_skip,page_size]}})
        return render_template('show_post.template.html',post=post,page_number=page_number,number_of_pages=number_of_pages)
    else:
        # Allow Users to Post Comments
        # Retrieve Information From the Comment Box Form
        comment = request.form.get('editordata')
        comment_soup = BeautifulSoup(comment,"html.parser")
        time_of_post = datetime.datetime.now()
        votes = int()

        # Validate the comment, check if the comment is empty
        if comment == "":
            flash('Error: Invalid Comment!','danger')
            return redirect(request.url)
        else:
            # Update the Post in the Database and add comments to the array
            db.Posts.update({
                '_id':ObjectId(post_id)
            },{
                '$push': {
                    'Comments':{
                        '_id': ObjectId(),
                        'Username': flask_login.current_user.username,
                        'Content': comment_soup.get_text(),
                        'Date_Posted': time_of_post,
                        'Votes': votes
                    }
                }

            })
            flash('Comment has been added successfully','success')
            return redirect(request.url)


# Allow Users to Edit their own post
@app.route('/edit/post/<post_id>',methods=['GET','POST'])
@flask_login.login_required
def edit_user_posts(post_id):
    if request.method == 'GET':
        user_post = db.Posts.find_one({
            '_id':ObjectId(post_id)
        })
        return render_template('edit_user_post.template.html',user_post=user_post)
    else:
        # Retrieving the information from the form
        title = request.form.get('title')
        content = request.form.get('editordata')
        content_soup = BeautifulSoup(content,"html.parser")

        # Form Field Validation
        # Check if the fields are empty, if the fields are empty raise the error
        # Accumulator
        errors = {}
        # Check if title is empty
        if title == "":
            flash('Error: Invalid Title','danger')
            errors.update(invalid_title="Title Field is Empty, please enter a valid title")
        # Check if content is empty
        elif content =="":
            flash("Error: Invalid Content",'danger')
            errors.update(invalid_content="Content Field is Empty,please enter a valid content")
        # If errors, redirect back to the create post page and raise error
        if len(errors) > 0:
            user_post = db.Posts.find_one({
                '_id':ObjectId(post_id)
            })  
            flash("Update Failure",'danger')
            return redirect(url_for('show_user_posts'))
        else:
            # If there are no errors, proceed to update the post
            db.Posts.update({
                '_id':ObjectId(post_id)
            },
                {
                    '$set': {
                        'Title': title,
                        'Content': content_soup.get_text()
                            }
                        }
            )
            flash("Your Post has been updated successfully","success")
            return redirect(url_for('show_user_posts'))




# Allow users to Delete their own post 
@app.route('/delete/<post_id>')
@flask_login.login_required
def delete_user_posts(post_id):
    db.Posts.remove({
            '_id':ObjectId(post_id)
        })
    flash("Your Post has been removed successfully","success")
    return redirect(url_for('show_user_posts'))



# Implement working Edit Comment, Delete Comment
@app.route('/edit/comment/<comment_id>',methods=['GET','POST'])
@flask_login.login_required
def edit_comment(comment_id):
    pipeline= [
        {
            "$unwind":"$Comments"
        },
        {
            "$match":{
                "Comments._id":ObjectId(comment_id)
            }
        },
        {
            '$project':{
                '_id':1,
                'PostID':0,
                'Title':0,
                'Content':0,
                'Votes':0,
                'Date_Posted':0,
                'Username':0
            }
        }
    ]
    cursor = db.Posts.aggregate(pipeline)
    results = list(cursor)
    for i in results:
            comment_data=i
    post_id = comment_data['_id']
    if request.method =="GET":
        user_post = comment_data.get('Comments', {}).get('Username')
        comment_post = comment_data.get('Comments',{})
        if flask_login.current_user.username == user_post:
            return render_template('edit_comment.template.html',comment_post=comment_post)
        else:
            flash('Error: Not Allowed to Edit Comment','danger')
            return redirect(url_for('show_post',post_id=post_id))
    else:
        # Receive the input from the form
        comment = request.form.get('editordata')
        comment_soup = BeautifulSoup(comment,"html.parser")

        # Validate the field, check if the comment is not empty. If the comment is empty, raise an error
        if comment == "":
            flash('Error: Invalid Comment!','danger')
            return redirect(request.url)
        else:
            comment_data.get('Comments', {}).get('_id')
            # If there are no errors, proceed to update the comment
            db.Posts.update({
                '_id':ObjectId(comment_data['_id']),
                'Comments.Content': str(comment_data.get('Comments', {}).get('Content')),
            },
                {'$set':{"Comments.$.Content":comment_soup.get_text()}}
            )
            flash('Comment has been updated successfully','success')
            return redirect(url_for('show_post',post_id=post_id))

@app.route('/delete/comment/<comment_id>')
@flask_login.login_required
def delete_comment(comment_id):
    pipeline= [
        {
            "$unwind":"$Comments"
        },
        {
            "$match":{
                "Comments._id":ObjectId(comment_id)
            }
        },
        {
            '$project':{
                '_id':1,
                'PostID':0,
                'Title':0,
                'Content':0,
                'Votes':0,
                'Date_Posted':0,
                'Username':0
            }
        }
    ]
    cursor = db.Posts.aggregate(pipeline)
    results = list(cursor)
    for i in results:
            comment_data=i
    post_id = comment_data['_id']
    user_post = comment_data.get('Comments', {}).get('Username')
     # Check if the user deleting is the user who made the comment
    if flask_login.current_user.username != user_post:
        flash('Error: Not Allowed to Delete Comment','danger')
        return redirect(url_for('show_post',post_id=post_id))
    else:
        # Allow the user to delete the comment
        db.Posts.update({
                '_id':ObjectId(comment_data['_id']),
                'Comments.Content': str(comment_data.get('Comments', {}).get('Content')),
            },
                {'$pull':
                    {"Comments":{
                        "_id":ObjectId(comment_data.get('Comments', {}).get('_id'))
                    }
                }})
        flash('Comment has been removed successfully','success')
        return redirect(url_for('show_post',post_id=post_id))
    

        





# Search Engine implementation for Posts

# Filter Search For Posts





# Implement a Upvote and Downvote button using AJAX
@app.route('/upvote',methods=['POST'])
@flask_login.login_required
def upvote_post():
    if request.method == "POST":
        data_received = json.loads(request.data)
        new_votes = int(data_received['Votes']) 
        post_id = data_received['PostID']
        # Update the votes in database
        db.Posts.update({
            '_id':ObjectId(post_id)
        },{
            '$set':{
                'Votes':new_votes
            }
        })
        return redirect(url_for('home'))

@app.route('/downvote',methods=['POST'])
@flask_login.login_required
def downvote_post():
    if request.method == "POST":
        data_received = json.loads(request.data)
        new_votes = int(data_received['Votes']) 
        post_id = data_received['PostID']
        # Update the votes in database
        db.Posts.update({
            '_id':ObjectId(post_id)
        },{
            '$set':{
                'Votes':new_votes
            }
        })
    return redirect(url_for('home'))


# Search Functionality for the Posts
@app.route('/home',methods=['POST'])
@flask_login.login_required
def search_post_home():
    # Get all the search terms
    # Search via post title or username
    if request.method =='POST':
        required_title = request.form.get('search') or ''
    # Creating the query based on the search terms
        criteria = {}

        if required_title:
            criteria['Title'] = {
                '$regex':required_title,
                '$options': 'i'
            }

        
        all_posts = db.Posts.find(criteria)
        return render_template('home.template.html',posts=all_posts)
        


# <----------------------------------------------------Listings----------------------------------------------------------------------->

@app.route('/marketplace')
def marketplace():
    listings= db.Listings.find()
    return render_template('marketplace.template.html',listings=listings)



brands_list=[
    'Please Select A Brand',
    'Rolex',
    'Casio',
    'Apple',
    'Seiko',
    'Timex',
    'Tudor',
    'Omega',
    'Audemars Piguet',
    'Panerai',
    'Tag Hauer',
    'Breitling',
    'Cartier',
    'Iwc',
    'Hublot',
    'Shinola',
    'Other Brands'
]

for i , word in enumerate(brands_list):
    brands_list[i]= word.upper()

@app.route('/create/listing',methods=['GET','POST'])
@flask_login.login_required
def create_listing():
    if request.method=='GET':
        # Loads the create listing form for the user
        return render_template('create_listing.template.html',errors={},countries=country_list, brands=brands_list,
                                cloud_name=CLOUD_NAME,upload_preset=UPLOAD_PRESET)
    else: 
        # Retrieve the values of the form 
        title = request.form.get('title')
        brand= request.form.get('brand')
        model = request.form.get('model')
        description= request.form.get('editordata')
        price = request.form.get('price')
        country=request.form.get('country')
        caption = request.form.get('caption')
        url_image= request.form.get('uploaded-file-url')
        asset_id=request.form.get('asset-id')



        # Check if the form entry is valid:
        # Accumulator
        errors={}
         # Check if title is empty
        if title == "":
            flash('Error: Invalid Title','danger')
            errors.update(invalid_title="Title Field is Empty, please enter a valid title")
        # check if brand field is not selected
        elif brand == "PLEASE SELECT A BRAND":
            flash('Error: Invalid Brand','danger')
            errors.update(invalid_brand="Brand cannot be empty, please select a valid brand")
        # check if model field is empty
        elif model =="":
            flash('Error: Invalid Model','danger')
            errors.update(invalid_model="Model field cannot be empty, please enter a valid model")
        # Check if description is empty
        elif description =="":
            flash("Error: Invalid Description",'danger')
            errors.update(invalid_description="Description Field is Empty,please enter a valid description")
        # Check if Image File is empty
        elif url_image=="":
            flash("Error: Invalid Image","danger")
            errors.update(invalid_image="Valid Image has to be uploaded, please upload an image")

        # If errors, redirect back to the create listing page and raise error
        if len(errors) > 0:
            flash("Create Failure",'danger')
            return redirect(url_for('create_listing'))
        # If no errors, insert listing data into database
        else:
            # Issues a random ID number for the profile ID that is unique and not repeated
            listing_number_list = list(range(1,max_capacity_users))
            random.shuffle(listing_number_list)
            listingID = listing_number_list.pop()
            dateposted = datetime.datetime.now()
            likes = int()
            description_soup = BeautifulSoup(description,"html.parser")


            new_listing = {
                'listingID':listingID,
                'Title':title,
                'Brand':brand,
                'Model':model,
                'Description':description_soup.get_text(),
                'Price': price,
                'Country': country,
                'Likes': likes,
                'Date_Posted':dateposted,
                'Username': flask_login.current_user.username,
                'Image_URL': url_image,
                'Asset_ID':asset_id,
                'Caption':caption
            }

            db.Listings.insert_one(new_listing)
            flash("Your Listing has been created", "success")
            return redirect(url_for('marketplace'))


@app.route('/like',methods=['POST'])
@flask_login.login_required
def like_post():
    if request.method == "POST":
        data_received = json.loads(request.data)
        new_likes = int(data_received['Likes'])
        listing_id = data_received['ListingID']
        # Update the votes in database
        db.Listings.update({
            '_id':ObjectId(listing_id)
        },{
            '$set':{
                'Likes':new_likes
            }
        })
        return redirect(url_for('marketplace'))


@app.route('/edit/listing/<listing_id>',methods=['GET','POST'])
@flask_login.login_required
def edit_listing(listing_id):
    listing = db.Listings.find_one({
            '_id':ObjectId(listing_id)
    })
    get_id = listing['_id']
    if request.method =='GET':
        return render_template('edit_listing.template.html',listing=listing,countries=country_list,brands=brands_list,
                                cloud_name=CLOUD_NAME,upload_preset=UPLOAD_PRESET)
    else:
        # Retrieve the updated information from the form
        title = request.form.get('title')
        description= request.form.get('editordata')
        price = request.form.get('price')
        country=request.form.get('country')
        caption = request.form.get('caption')
        url_image= request.form.get('uploaded-file-url')
        asset_id=request.form.get('asset-id')
        # Validate the form inputs

        # Check if the form entry is valid:
        # Accumulator
        errors={}
         # Check if title is empty
        if title == "":
            flash('Error: Invalid Title','danger')
            errors.update(invalid_title="Title Field is Empty, please enter a valid title")
        # Check if description is empty
        elif description =="":
            flash("Error: Invalid Description",'danger')
            errors.update(invalid_description="Description Field is Empty,please enter a valid description")
        # Check if Image File is empty
        elif url_image=="":
            flash("Error: Invalid Image","danger")
            errors.update(invalid_image="Valid Image has to be uploaded, please upload an image")

        # If errors, redirect back to the create listing page and raise error
        if len(errors) > 0:
            flash("Update Failure",'danger')
            return redirect(url_for('edit_listing',listing_id=ObjectId(get_id)))
        # If no errors, insert listing data into database
        else:
            # Update the listing
            description_soup = BeautifulSoup(description,"html.parser")
            db.Listings.update({
                '_id':ObjectId(listing_id)
            },
                {
                    '$set': {
                        'Title': title,
                        'Description': description_soup.get_text(),
                        'Price': price,
                        'Country': country,
                        'Image_URL': url_image,
                        'Asset_ID':asset_id,
                        'Caption':caption
                        }
                }
            )
            flash("Your Listing has been updated successfully","success")
            return redirect(url_for('show_user_listings'))


@app.route('/delete/listing/<listing_id>')
@flask_login.login_required
def delete_listing(listing_id):
    db.Listings.remove({
        '_id':ObjectId(listing_id)
    })
    return redirect(url_for('show_user_listings'))


@app.route('/mylistings')
def show_user_listings():
    # Get Total number of results based on database
    number_of_results = db.Listings.find({
        'Username':flask_login.current_user.username
    }).count()
    page_size = 2
    number_of_pages = math.ceil(number_of_results/page_size)-1
    # Get the current page number from the args get request, if it does not exist set it to zero
    page_number = request.args.get('page_number') or '0'
    page_number = int(page_number)
    # calculate how many results will be skipped depending on page number
    number_to_skip = page_number * page_size

    user_listings = db.Listings.find({
        'Username':flask_login.current_user.username
    }).skip(number_to_skip).limit(page_size)

    return render_template('user_listings.template.html',user_listings=user_listings,
                            page_number=page_number,number_of_pages=number_of_pages)



@app.route('/listing/<listing_id>',methods=['GET','POST'])
@flask_login.login_required
def show_listing(listing_id):
    listing = db.Listings.find_one({
            '_id':ObjectId(listing_id)
        })
    if request.method =="GET":
        return render_template('show_listing.template.html',listing=listing)



# Search Functionality for the Posts
@app.route('/marketplace',methods=['POST'])
@flask_login.login_required
def search_listings_marketplace():
    # Get all the search terms
    # Search via post title or username
    if request.method =='POST':
        required_title = request.form.get('search') or ''
    # Creating the query based on the search terms
        criteria = {}

        if required_title:
            criteria['Title'] = {
                '$regex':required_title,
                '$options': 'i'
            }

        
        all_listings = db.Listings.find(criteria)
        return render_template('marketplace.template.html',listings=all_listings)

@app.route('/search',methods=['GET','POSt'])
def search():
    pass

if __name__ == "__main__":
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)