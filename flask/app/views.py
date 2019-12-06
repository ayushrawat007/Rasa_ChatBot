from flask import request, redirect, flash, request, jsonify, make_response, abort, render_template, session
from flask_mysqldb import MySQL
from app import chatBot
import yaml as ym
import os
from passlib.hash import sha256_crypt
import re, datetime
import collections
import os

from sklearn.externals import joblib
import en_core_web_sm
import numpy as np
import pandas as pd
import spacy

# project_dir = os.path.dirname(os.path.abspath(__file__))

filename = 'flask/app/db.yml'
db = ym.safe_load(open(filename))
chatBot.config['MYSQL_HOST'] = db['mysql_host']
chatBot.config['MYSQL_USER'] = db['mysql_user']
chatBot.config['MYSQL_PASSWORD'] = db['mysql_password']
chatBot.config['MYSQL_DB'] = db['mysql_db']
mysql = MySQL(chatBot)
chatBot.secret_key = 'key'
chatBot.config["SECRET_KEY"] = 'pgAQJriQYZR0AkpqK3Geqw'




@chatBot.route("/",methods=["GET","POST"])
def root():
    
    return render_template('public/template/public_template.html')

@chatBot.route("/chatBot",methods=["GET","POST"])
def bot_reply():

    nlp = spacy.load("en_core_web_sm")
    loaded_model=joblib.load('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\model\\model.pkl')
    print("In bot_reply")
    details = request.get_json() 
    print(details)
    prediction=loaded_model.predict(nlp(details["query"]).vector.reshape(1,384))
    res = make_response(jsonify({"intent":str(prediction[0])}), 200)
    return res 


   

    




