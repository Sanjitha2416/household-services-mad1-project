from sqlite3 import IntegrityError
from flask import Flask, render_template, request,url_for,redirect
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
            return redirect(url_for("admin_dashboard",name=uname))
        elif usr and usr.role==1:
            return redirect(url_for("user_dashboard",name=uname))
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

        # Check if the user already exists
        usr = CustomerDetails.query.filter_by(email=uname).first()
        if usr:
            return render_template("user_signup.html", msg="This mail id is already registered")

        # Try adding the new user
        try:
            new_usr = CustomerDetails(email=uname, password=pwd, name=fn, address=add, pincode=pin)
            db.session.add(new_usr)
            db.session.commit()
            return render_template("login.html", msg="Thank you for registering. You can login now!")
        
        except IntegrityError:
            db.session.rollback()  # Roll back the session to avoid issues
            return render_template("user_signup.html", msg="This mail id is already registered")
    
    return render_template("user_signup.html",msg="")


@app.route("/registerp")
def signupp():
    return render_template("professional_signup.html")

#Common route for admin_dashboard
@app.route("/admin/<name>")
def admin_dashboard(name):
    services=get_services()
    return render_template("admin_dashboard.html",name=name,services=services)

@app.route("/user/<name>")
def user_dashboard(name):
    return render_template("user_dashboard.html",name=name)

@app.route("/service/<name>",methods=["POST","GET"])
def add_service(name):
    if request.method=="POST":
        sname=request.form.get("name")
        description=request.form.get("description")
        price=request.form.get("base_price")
        new_service=Service(name=sname, description=description, base_price=price)
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for("admin_dashboard",name=name))
    
    return render_template("add_service.html",name=name)

def get_services():
    services=Service.query.all()
    return services