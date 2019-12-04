from flask import request, redirect, flash, request, jsonify, make_response, abort, render_template, session
from app import chatBot

@chatBot.route("/",method=["GET"])
def root():
    return "Test"