from flask import Flask, render_template,request,redirect,url_for
import os
import pymongo
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

app= Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

MONGO_URI= os.environ.get('MONGO_URI')
DB_NAME = "Timeless"


client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]




if __name__ == "__main__":
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)