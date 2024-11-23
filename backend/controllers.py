from flask import Flask, render_template, request
from .models import *
from flask import current_app as app

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login",methods=["GET","POST"])
def signin():
    if request.method=="POST":
        uname =request.form.get("user_name")
        pwd =request.form.get("password")
        usr=CustomerDetails.query.filter_by(email=uname, password=pwd).first()
        if usr and usr.role==0:
            return render_template("admin_dashboard.html")
        elif usr and usr.role==1:
            return render_template("user_dashboard.html")
        else:
            return render_template("login.html",msg="Invalid user credentials")

    return render_template("login.html",msg="")

@app.route("/register", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        uname =request.form.get("user_name")
        pwd =request.form.get("password")
        fn =request.form.get("name")
        add =request.form.get("address")
        pin=request.form.get("pincode")
        usr=CustomerDetails.query.filter_by(email=uname, password=pwd).first()
        if usr:
            return render_template("user_signup.html",msg="This mail id is already registered")
        new_usr=CustomerDetails(email=uname,password=pwd,name=fn,address=add,pincode=pin)
        db.session.add(new_usr)
        db.session.commit()
        return render_template("login.html",msg="Thank you for registering. You can login now!")
    
    return render_template("user_signup.html",msg="")


@app.route("/registerp")
def signupp():
    return render_template("professional_signup.html")