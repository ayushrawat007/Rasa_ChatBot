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
from flask import g
import numpy as np
import csv
import json
from datetime import date

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

init=0
airline=1
destination_info=2


#State Policy
state={
    (init,"atis_flight"):(airline,"In which Airline do you want to book the flight ?"),
    (airline,"no_intent"):(destination_info,"Please specify the Location date    time for the booking?"),
    (destination_info,"no_intent"):(init,"Booking done ......Thank you for your time you can download the tickets from the following link www.random.com")

}


@chatBot.context_processor
def context_processor():
    return dict(key='value')

def openfile(path,permission):
    with open(path,permission) as f:
        if path.endswith('.csv'):
            reader = csv.reader(f)
            data = list(reader)
        if path.endswith('.json'):
            data=json.load(f)
    f.close()
    return data

def writefile(obj,path,permission):

    with open(path, permission) as outfile:
        json.dump(obj, outfile)
    outfile.close()

def predict_intent(query):
    nlp = spacy.load("en_core_web_sm")
    loaded_model=joblib.load('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\model\\model.pkl')
    prediction=loaded_model.predict(nlp(query).vector.reshape(1,384)) 
    return prediction

def get_response_object(answer):
    res = make_response(jsonify({"what_to_ask":answer}), 200)
    return res


def extract_entity(query,entity_type):
    nlp=spacy.load('en')
    doc=nlp(query.title())
    # doc=nlp(details["query"].title())
    count=0
    gpe=list()
    for ent in doc.ents:
        if ent.label_==entity_type:
                gpe.append(ent.text)
                count+=1
    if count==2:
        departure=gpe[0]
        destination=gpe[1]
        return (departure,destination)
    return ("not_allowed","")
    

@chatBot.route("/",methods=["GET","POST"])
def root():
    airline_list=openfile('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airline.csv','rt')

    session["state"]=0
    session["airline"]=""
    session["list_of_airline"]=airline_list

    return render_template('public/template/chatbot.html')


@chatBot.route("/chatBot",methods=["GET","POST"])
def bot_reply():
    details = request.get_json() 

    if details["query"]=="quit":
        session["state"]=0
        session["airline"]=""
        res=get_response_object("What else can I help you with ?")
        return res

    if session["state"]==0:
        prediction=predict_intent(details["query"])

        if(str(prediction[0])=="flight_booking"):
            session["state"]=1
            session["intent"]="flight_booking"
            res=get_response_object("In which Airline do you want to book the flight ?")
            return res
       

    if session["state"]==1:
        prediction=predict_intent(details["query"])

        if(str(prediction[0])=="flight_booking"):
            session["state"]=1
            res=get_response_object("In which Airline do you want to book the flight ?")
            return res

        # Next step we can check if we support this booking for the specified airline or not other wise return to session["state"] 0

        if(str(prediction[0])=="bogus"):
            airline_list=list(session["list_of_airline"][0])
            airline=details["query"]
            if airline in airline_list:
                session["airline"]=airline
                session["state"]=2
                res=get_response_object("Please specify the Location date and time for the booking?")
                return res
            airlines_string=','.join(airline_list)
            res=get_response_object("We don't server this Airline.Please select from the following.\n" + airlines_string)
            return res
    
    if session["state"]==2:
        if extract_entity(details["query"],"GPE")[0]!="not_allowed":
            session["departure"],session["destination"]=extract_entity(details["query"],"GPE")
        else:
            res=get_response_object("Please specify the Location correctly for the booking?")
            return res

        if(session["airline"]=="indigo"):
            data=openfile('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\indigo.json','rt')

        elif session["airline"]=="airasia":
            data=openfile('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airasia.json','rt')
        
        retur_str=""

        for flight in data:
            if session["departure"]==data[flight]["departure"] and session["destination"] == data[flight]["destination"]:
                retur_str=flight+" , Fare->"+data[flight]["charge"]+" Time->"+data[flight]["time"]

        if retur_str=="":
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json') as json_file:
                unanswere_query = json.load(json_file)
            if session["intent"] not in unanswere_query:
                unanswere_query[session["intent"]]={}
            if session["airline"] not in unanswere_query[session["intent"]]:
                unanswere_query[session["intent"]][session["airline"]]=[]
            my_date=str(date.today())
            unanswere_query[session["intent"]][session["airline"]].append({
                'query':details["query"],
                'date': my_date

            })

            session["state"]=2
            
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json', 'w') as outfile:
                json.dump(unanswere_query, outfile)    
            res = make_response(jsonify({"what_to_ask":"There are no flights available for this route.What else can I help you with?\n" }), 200)
            return res

        res = make_response(jsonify({"what_to_ask":"-------------Following flights are available in "+session["airline"]+"------------\n" + retur_str }), 200)
        return res

        #Extract the to and from from regex and check for date ,day and time 
        #if not present ask for the same :
        #if it is a invalid request return to the 1 session["state"] and ask to all the details again
        res = make_response(jsonify({"what_to_ask":"Booking done ......Thank you for your time you can download the tickets from the following link www.random.com"}), 200)
        session["state"]==0
        return res

    res=res = make_response(jsonify({"what_to_ask":"I dont understand"}), 200)
    return res 



@chatBot.route("/dashboard",methods=["GET","POST"])
def data_fill():
    uq=openfile('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json','rt')
    if request.method == "POST":
        details = request.form
        answer_list=details["answer"].split(",")
        nlp=spacy.load('en')
        doc=nlp(details["unansweredquery"].title())
        print("----------------before json load -----------------------")
        if details["airline"]=='indigo':
            airline_data=openfile('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\indigo.json','rt')
        if details["airline"]=='airasia':
            airline_data=openfile('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airasia.json','rt')
        
        print("----------------before entity extraction -----------------------")

        if extract_entity(details["unansweredquery"],"GPE")[0]!="not_allowed":
            departure,destination=extract_entity(details["unansweredquery"],"GPE")
            print("---------entity  extracted----------")
            airline_data[answer_list[0]]={
                "departure": departure,
                "destination": destination,
                "time": answer_list[1],
                "charge":answer_list[2] 
            }
            try:
                for queries in uq[details["intent"]][details["airline"]]:
                    if queries["query"]==details["unansweredquery"]:
                        uq[details["intent"]][details["airline"]].remove(queries)
            except KeyError:
                print("----------------------Key Error Occured-----------------")
                pass
        
            print("----------------before json dump  -----------------------")
            if details["airline"]=="indigo":
                writefile(airline_data,'G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\indigo.json','w')
            if details["airline"]=="airasia":
                writefile(airline_data,'G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airasia.json','w')
            writefile(uq,'G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json','w')
        
    return render_template('public/template/dashboard.html',uq=uq)