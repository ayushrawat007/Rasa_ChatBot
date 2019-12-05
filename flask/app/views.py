from flask import request, redirect, flash, request, jsonify, make_response, abort, render_template, session
from app import chatBot
import os
#project_dir = os.path.dirname(os.path.abspath(__file__))
@chatBot.route("/",methods=["GET"])
def root():
    return render_template('public/template/public_template.html')

