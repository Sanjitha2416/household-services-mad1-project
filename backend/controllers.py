from sqlite3 import IntegrityError
from flask import Flask, flash, render_template, request,url_for,redirect
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
    services=Service.query.all()
    pending_professionals = ProfessionalDetails.query.filter_by(status='Pending').all()
    return render_template("admin_dashboard.html", name=name, services=services, pending_professionals=pending_professionals)


@app.route("/service/<name>", methods=["POST", "GET"])
def add_service(name):
    if request.method == "POST":
        sname = request.form.get("name")
        description = request.form.get("description")

        # Create and save the main service
        new_service = Service(name=sname, description=description)
        db.session.add(new_service)
        db.session.commit()

        # Retrieve subcategories data
        subcat_names = request.form.getlist("subcat_name[]")
        subcat_descs = request.form.getlist("subcat_desc[]")
        subcat_prices = request.form.getlist("subcat_price[]")

        # Save subcategories with prices
        for subcat_name, subcat_desc, subcat_price in zip(subcat_names, subcat_descs, subcat_prices):
            subcategory = Subcategory(
                service_id=new_service.id,
                name=subcat_name,
                description=subcat_desc,
                price=subcat_price,
            )
            db.session.add(subcategory)
        db.session.commit()

        return redirect(url_for("admin_dashboard", name=name))
    
    return render_template("add_service.html", name=name)


@app.route("/edit_service/<int:service_id>/<name>", methods=["GET", "POST"])
def edit_service(service_id, name):
    service = Service.query.get(service_id)
    if not service:
        return "Service not found!", 404
    
    if request.method == "POST":
        service.name = request.form.get("name")
        service.description = request.form.get("description")
        service.base_price = request.form.get("base_price")
        db.session.commit()
        return redirect(url_for("admin_dashboard",name=name)) 

    return render_template("edit_service.html", service=service)


@app.route("/delete_service/<int:service_id>/<name>", methods=["POST"])
def delete_service(service_id, name):
    service = Service.query.get(service_id)
    if not service:
        return "Service not found!", 404

    # Optional: Delete associated subcategories if needed
    subcategories = Subcategory.query.filter_by(service_id=service_id).all()
    for subcategory in subcategories:
        db.session.delete(subcategory)

    # Now delete the service
    db.session.delete(service)
    db.session.commit()
    
    # Redirect to the admin dashboard after deleting the service
    return redirect(url_for("admin_dashboard", name=name))


@app.route("/register_professional", methods=["GET", "POST"])
def register_professional():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        service = request.form.get("service")
        experience = int(request.form.get("experience"))
        address = request.form.get("address")
        pincode = request.form.get("pincode")        

        # Check if email is already registered
        if ProfessionalDetails.query.filter_by(email=email).first():
            return "Email already registered!", 400

        # Add to the database
        new_professional = ProfessionalDetails(
            name=name,
            email=email,
            password=password,
            service=service,
            experience=experience,
            address=address,
            pincode=pincode,
            status="Pending"
        )
        db.session.add(new_professional)
        db.session.commit()
        return render_template('professional_signup.html', message="Registration successful! You can now log in below.", login_link=True)

    return render_template("professional_signup.html")


@app.route("/approve_professional/<int:professional_id>/<name>", methods=["POST"])
def approve_professional(professional_id, name):
    professional = ProfessionalDetails.query.get(professional_id)
    if professional:
        professional.status = "Approved"
        db.session.commit()
    return redirect(url_for("admin_dashboard", name=name))


@app.route("/reject_professional/<int:professional_id>/<name>", methods=["POST"])
def reject_professional(professional_id, name):
    professional = ProfessionalDetails.query.get(professional_id)
    if professional:
        professional.status = "Rejected"
        db.session.commit()
    return redirect(url_for("admin_dashboard", name=name))


@app.route('/search', methods=['POST'])
def search():
    search_by = request.form.get('search_by')
    search_query = request.form.get('search_query')
    results = []

    if search_by == 'services':
        results = db.session.query(
        Service.name,
        Service.description,
        Subcategory.name.label('subcategory_name'),
        Subcategory.price.label('subcategory_price')
        ).join(
        Subcategory, Subcategory.service_id == Service.id
        ).filter(
        Service.name.like(f"%{search_query}%")
         ).all()
        
    elif search_by == 'customers':
        results = db.session.query(CustomerDetails.name, CustomerDetails.email, 
                                   CustomerDetails.address, CustomerDetails.pincode) \
            .filter(CustomerDetails.name.like(f"%{search_query}%")).all()

    elif search_by == 'professionals':
        if search_query:  # If there is a search term
                # Filter based on name or status (approved or pending)
            results = ProfessionalDetails.query.filter(
                (ProfessionalDetails.name.ilike(f"%{search_query}%")) | 
                (ProfessionalDetails.status.ilike(f"%{search_query}%"))
            ).all()
        else:  # If no search term is provided, return all professionals
            results = ProfessionalDetails.query.all()

    return render_template('search.html', results=results, search_by=search_by)

# Optional GET route to render the search form without any query
@app.route('/search', methods=['GET'])
def search_form():
    return render_template('search.html')

def search_services(search_text):
    # Query services based on search_text
    return Service.query.filter(Service.name.contains(search_text)).all()

def search_customers(search_text):
    # Query customers based on search_text
    
    return CustomerDetails.query.filter(CustomerDetails.name.contains(search_text)).all()

def search_professionals(search_text):
    # Query professionals based on search_text
    return ProfessionalDetails.query.filter(ProfessionalDetails.name.contains(search_text)).all()


@app.route("/user/<name>")
def user_dashboard(name):
    services=Service.query.all()
    return render_template("user_dashboard.html",name=name,services=services)


@app.route("/book_service/<customer_id>/<service_id>/<name>", methods=["GET", "POST"])
def book_service(customer_id, service_id, name):
    if request.method == "POST":
        # Process service booking
        subcategory_id = request.form.get("subcategory_id")
        
        # Check service and subcategory validity
        service = Service.query.filter_by(id=service_id).first()
        if not service:
            return "Service not found", 404

        # Assign an available professional
        professional = ProfessionalDetails.query.filter_by(service_id=service_id, is_available=True).first()
        if not professional:
            return "No professionals available for this service.", 404

        # Create the service request
        new_request = ServiceRequest(
            customer_id=customer_id,
            service_id=service_id,
            subcategory_id=subcategory_id,
            professional_id=professional.id,
            status="Requested"
        )
        db.session.add(new_request)

        # Mark professional as unavailable
        professional.is_available = False
        db.session.commit()

        return redirect(url_for("user_dashboard", name=name))

    # GET method: Show booking form
    service = Service.query.filter_by(id=service_id).first()
    if not service:
        return "Service not found", 404

    subcategories = Subcategory.query.filter_by(service_id=service_id).all()
    available_professionals = ProfessionalDetails.query.filter_by(service_id=service_id, is_available=True).count()

    return render_template(
        "book_service.html",
        customer_id=customer_id,
        service_id=service_id,
        name=name,
        service_name=service.name,
        subcategories=subcategories,
        available_professionals=available_professionals
    )
