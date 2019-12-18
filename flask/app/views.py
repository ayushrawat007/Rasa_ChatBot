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

@chatBot.route("/",methods=["GET","POST"])
def root():
    
    with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airline.csv', 'rt') as f:
        reader = csv.reader(f)
        airline_list = list(reader)

    session["state"]=0
    session["airline"]=""
    session["list_of_airline"]=airline_list

    print("------------------------------")
    print(airline_list)
    
    return render_template('public/template/chatbot.html')





@chatBot.route("/chatBot",methods=["GET","POST"])
def bot_reply():

    details = request.get_json() 
    if details["query"]=="quit":
        session["state"]=0
        session["airline"]=""
        res = make_response(jsonify({"what_to_ask":"What else can I help you with ?"}), 200)

        return res


    if session["state"]==0:
        nlp = spacy.load("en_core_web_sm")
        loaded_model=joblib.load('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\model\\model.pkl')
        print("In bot_reply")
        print(details)
        prediction=loaded_model.predict(nlp(details["query"]).vector.reshape(1,384)) 
        if(str(prediction[0])=="flight_booking"):
            session["state"]=1
            session["intent"]="flight_booking"
            res = make_response(jsonify({"intent":str(prediction[0]),"what_to_ask":"In which Airline do you want to book the flight ?"}), 200)
            return res
       

    if session["state"]==1:
        nlp = spacy.load("en_core_web_sm")
        loaded_model=joblib.load('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\model\\model.pkl')
        prediction=loaded_model.predict(nlp(details["query"]).vector.reshape(1,384))

        if(str(prediction[0])=="flight_booking"):
            session["state"]=1
            res = make_response(jsonify({"intent":str(prediction[0]),"what_to_ask":"In which Airline do you want to book the flight ?"}), 200)
            return res
        
        
        # Next step we can check if we support this booking for the specified airline or not other wise return to session["state"] 0
        
        if(str(prediction[0])=="bogus"):
            airline_list=list(session["list_of_airline"][0])
            airline=details["query"]
            if airline in airline_list:
                session["airline"]=airline
                session["state"]=2
                res = make_response(jsonify({"what_to_ask":"Please specify the Location date and time for the booking?"}), 200)
                return res
            
            airlines_string=','.join(airline_list)
            print(airlines_string)
            res = make_response(jsonify({"what_to_ask":"We don't server this Airline.Please select from the following.\n" + airlines_string }), 200)
            return res
    
    if session["state"]==2:
        nlp=spacy.load('en')
        
        doc=nlp(details["query"].title())
        count=0
        gpe=list()
        for ent in doc.ents:
            if ent.label_=="GPE":
                gpe.append(ent.text)
                count+=1
        if count==2:
            session["departure"]=gpe[0]
            session["destination"]=gpe[1]
        else:
            res = make_response(jsonify({"what_to_ask":"Please specify the Location correctly for the booking?"}), 200)
            return res

        print(session["departure"],session["destination"])

        if(session["airline"]=="indigo"):
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\indigo.json') as json_file:
                data = json.load(json_file)
                print(data)

        elif session["airline"]=="airasia":
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airasia.json') as json_file:
                data = json.load(json_file)
        
        retur_str=""

        for flight in data:
            
            print(data[flight]["departure"],data[flight]["destination"])
            if session["departure"]==data[flight]["departure"] and session["destination"] == data[flight]["destination"]:
                retur_str=flight+" , Fare->"+data[flight]["charge"]+" Time->"+data[flight]["time"]

        if retur_str=="":
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json') as json_file:
                unanswere_query = json.load(json_file)
            print(unanswere_query)
            if session["intent"] not in unanswere_query:
                unanswere_query[session["intent"]]={}
            if session["airline"] not in unanswere_query[session["intent"]]:
                unanswere_query[session["intent"]][session["airline"]]=[]
            my_date=str(date.today())
            unanswere_query[session["intent"]][session["airline"]].append({
                'query':details["query"],
                'date': my_date

            })

            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json', 'w') as outfile:
                json.dump(unanswere_query, outfile)
           
            session["state"]=1
            
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
    with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json') as json_file:
        uq = json.load(json_file)

    if request.method == "POST":
        details = request.form
        print(details)
        print(details["unansweredquery"])
        print(details["answer"])

        answer_list=details["answer"].split(",")
        print(answer_list)
        
        nlp=spacy.load('en')
        print(details["unansweredquery"])
        doc=nlp(details["unansweredquery"].title())
            
        print("----------------before json load -----------------------")
        if details["airline"]=='indigo':
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\indigo.json') as json_file:
                airline_data = json.load(json_file)
        if details["airline"]=='airasia':
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airasia.json') as json_file:
                airline_data = json.load(json_file)
        count=0
        print("----------------before entity extraction -----------------------")
        gpe=[]
        for ent in doc.ents:
            if ent.label_=="GPE":
                gpe.append(ent.text)
                count+=1
        print("----------------before json load -----------------------")
        if count==2:
            
            departure=gpe[0]
            destination=gpe[1]
            print("---------entity  extracted----------")

            airline_data[answer_list[0]]={
                "departure": departure,
                "destination": destination,
                "time": answer_list[1],
                "charge":answer_list[2] 
            }
            
            print("----------------------------------------------------------------------------")
            print(airline_data)
            try:
                for queries in uq[details["intent"]][details["airline"]]:
                    if queries["query"]==details["unansweredquery"]:
                        uq[details["intent"]][details["airline"]].remove(queries)
            except KeyError:
                print("----------------------Key Error Occured-----------------")
                pass
            print("----------------before json dump  -----------------------")
            if details["airline"]=="indigo":
                with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\indigo.json', 'w') as outfile:
                    json.dump(airline_data, outfile)

            if details["airline"]=="airasia":
                with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\airasia.json', 'w') as outfile2:
                    json.dump(airline_data, outfile2)
            
            with open('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\data\\unanswered_queries.json', 'w') as outfile3:
                    json.dump(uq, outfile3)


    return render_template('public/template/dashboard.html',uq=uq)


    
    # details = request.get_json() 
    # if details["query"]=="quit":
    #     session["state"]=0
    #     res = make_response(jsonify({"what_to_ask":"What else can I help you with ?"}), 200)
    #     return res
    # if session["state"]==0:
    #     nlp = spacy.load("en_core_web_sm")
    #     loaded_model=joblib.load('G:\\Users\\Ayush\\PycharmProjects\\Real_Project_ChatBot\\flask\\app\\model\\model.pkl')
    #     print("In bot_reply")
    #     print(details)
    #     prediction=loaded_model.predict(nlp(details["query"]).vector.reshape(1,384)) 
    #     if(str(prediction[0])=="flight_booking"):
    #         session["state"]=1
    #         res = make_response(jsonify({"intent":str(prediction[0]),"what_to_ask":"In which Airline do you want to book the flight ?"}), 200)
    #         return res
    
    # if session["state"]==1:
    #     airline=details["query"]
    #     # Next step we can check if we support this booking for the specified airline or not other wise return to session["state"] 0
    #     session["state"]=2
    #     res = make_response(jsonify({"what_to_ask":"Please specify the Location date and time for the booking?"}), 200)
    #     return res
    # if session["state"]==2:
    #     #Extract the to and from from regex and check for date ,day and time 
    #     #if not present ask for the same :
    #     #if it is a invalid request return to the 1 session["state"] and ask to all the details again
    #     res = make_response(jsonify({"what_to_ask":"Booking done ......Thank you for your time you can download the tickets from the following link www.random.com"}), 200)
    #     session["state"]==0
    #     return res
    



   

    




