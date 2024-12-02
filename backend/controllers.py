from sqlite3 import IntegrityError
from flask import Flask, flash, render_template, request,url_for,redirect
from .models import *
from flask import current_app as app
import matplotlib
matplotlib.use('Agg')  #generates plots as image files without relying on a GUI, preventing conflicts with Flask's multithreading
import matplotlib.pyplot as plt

@app.route("/")
def home():
    return render_template("index.html")

#login routing
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
        
        prof = ProfessionalDetails.query.filter_by(email=uname, password=pwd).first()
        if prof:
            if prof.role == 2:  # Professional has role 2
                return redirect(url_for("professional_dashboard", email=uname))
        else:
            return render_template("login.html",msg="Invalid user credentials")

    return render_template("login.html",msg="")

#customer registration
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

#professional registration
@app.route("/registerp")
def signupp():
    return render_template("professional_signup.html")


#Common route for admin_dashboard
@app.route("/admin/<name>")
def admin_dashboard(name):
    services=Service.query.all()
    pending_professionals = ProfessionalDetails.query.filter_by(status='Pending').all()
    return render_template("admin_dashboard.html", name=name, services=services, pending_professionals=pending_professionals)

#adding a service
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

#editing a service
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

#deleting a service
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
    customer = CustomerDetails.query.filter_by(email=name).first()
    service_history = db.session.query(
        ServiceRequest.id,
        Service.name.label("service_name"),
        ProfessionalDetails.name.label("professional_name"),
        ServiceRequest.date_time,
        ServiceRequest.status
    ).join(Service, ServiceRequest.service_id == Service.id) \
     .join(ProfessionalDetails, ServiceRequest.professional_id == ProfessionalDetails.id) \
     .filter(ServiceRequest.customer_id == customer.id) \
     .all()

    return render_template("user_dashboard.html",name=name,services=services,customer=customer,service_history=service_history)

@app.route("/book_service/<int:customer_id>/<int:service_id>/<int:subcategory_id>/<name>", methods=["GET", "POST"])
def book_service(customer_id, service_id, subcategory_id, name):
    # Fetch the customer details
    customer = CustomerDetails.query.filter_by(email=name).first()
    customer = CustomerDetails.query.get(customer_id)
    if not customer:
        return "Customer not found", 404

    # Fetch the service details
    service = Service.query.get(service_id)
    if not service:
        return "Service not found", 404

    # Fetch the subcategory details
    subcategory = next((s for s in service.subcategories if s.id == subcategory_id), None)
    if not subcategory:
        return "Subcategory not found", 404
    
    
    # Fetch the professional details for this service and subcategory
    professionals = ProfessionalDetails.query.filter_by(
        service_id=service.id, 
        is_available='TRUE', 
        status='Approved'
    ).all()
    if not professionals:
        return "No professionals available", 404

    professional = professionals[0]

    if request.method == "POST":
        # Get form data (address and date/time)
        address = request.form.get("address")
        date_time_str = request.form.get("date_time")
        date_time_obj = datetime.fromisoformat(date_time_str)

        # Create the service request
        new_request = ServiceRequest(
            date_time=date_time_obj,
            address=address,
            status="Requested",
            customer_id=customer.id,
            service_id=service_id,
            professional_id=professional.id
        )

        db.session.add(new_request)

        # Mark the professional as unavailable
        professional.is_available = False
        db.session.commit()

        # Redirect to user dashboard with success message
        return redirect(f"/user/{name}")

    return render_template("book_service.html", customer_id=customer_id, service_id=service_id, subcategory_id=subcategory_id, service_name=service.name, subcategory_name=subcategory.name, name=customer.email)

@app.route("/close_service/<int:service_id>", methods=["POST"])
def close_service(service_id):
    service_request = ServiceRequest.query.get(service_id)
    if not service_request:
        return "Service request not found", 404
    
    # Update the status of the service request to 'Closed'
    service_request.status = "Closed"
    professional = ProfessionalDetails.query.get(service_request.professional_id)
    if professional:
        professional.is_available = "TRUE" 
    db.session.commit()
    
    return redirect(f"/user/{service_request.customer.email}")


from sqlalchemy import or_, cast, String
@app.route("/user_search/<name>", methods=["GET", "POST"])
def user_search(name):
    query = request.form.get("query")
    search_results = None
    request_history = None

    customer = CustomerDetails.query.filter_by(email=name).first()
    if not customer:
        return "User not found", 404

    if query:
        # Search for service subcategories
        search_results = Subcategory.query.filter(Subcategory.name.ilike(f"%{query}%")).all()

        # Search for previous requests based on query matching status, service name, or date
        request_history = db.session.query(
            ServiceRequest.id,
            Service.name.label("service_name"),
            ServiceRequest.date_time,
            ServiceRequest.status
        ).join(Service, ServiceRequest.service_id == Service.id) \
         .filter(
             ServiceRequest.customer_id == customer.id,
             or_(
                 Service.name.ilike(f"%{query}%"),
                 ServiceRequest.status.ilike(f"%{query}%"),
                 cast(ServiceRequest.date_time, String).ilike(f"%{query}%")
             )
         ).all()

    return render_template("user_search.html", query=query, search_results=search_results, request_history=request_history,name=name)


@app.route("/remarks/<int:service_id>", methods=["GET", "POST"])
def remarks_page(service_id):
    # Fetch the service request by ID
    service_request = ServiceRequest.query.get(service_id)
    if not service_request:
        return "Service request not found", 404

    # Check if the service has subcategories
    subcategory_name = None
    if service_request.service and service_request.service.subcategories:
        subcategory_name = service_request.service.subcategories[0].name  # Change this logic if needed

    if request.method == "POST":
        # Handle feedback submission
        rating = int(request.form.get("rating"))
        remark = request.form.get("remark")

        # Save feedback
        feedback = Feedback(rating=rating, remark=remark, request_id=service_id)
        db.session.add(feedback)

        # Close the service request
        service_request.status = "Closed"
        professional = ProfessionalDetails.query.get(service_request.professional_id)
        if professional:
            professional.is_available = True
        db.session.commit()

        return redirect(f"/user/{service_request.customer.email}")

    # Render the remarks form with the service request and subcategory name
    return render_template("remarks.html", service_request=service_request, subcategory_name=subcategory_name)

#approved professional dashboard
@app.route("/professional_dashboard/<email>")
def professional_dashboard(email):
    professional = ProfessionalDetails.query.filter_by(email=email).first()
    
    if not professional:
        return "Professional not found", 404

    if professional.status != 'Approved':
        return redirect(url_for('pending_approval'))  # Redirect to Pending Approval page
    
    upcoming_services = (
        ServiceRequest.query
        .filter_by(professional_id=professional.id, status='Requested')
        .join(CustomerDetails, ServiceRequest.customer_id == CustomerDetails.id)
        .add_columns(
            ServiceRequest.id, ServiceRequest.date_time, 
            ServiceRequest.address.label("location"), 
            CustomerDetails.name.label("customer_name")
        ).all()
    )

    closed_services = (
        ServiceRequest.query
        .filter_by(professional_id=professional.id, status='Closed')
        .join(CustomerDetails, ServiceRequest.customer_id == CustomerDetails.id)
        .join(Feedback, ServiceRequest.id == Feedback.request_id, isouter=True)
        .add_columns(
            ServiceRequest.id, ServiceRequest.date_time, 
            ServiceRequest.address.label("location"), 
            CustomerDetails.name.label("customer_name"), 
            Feedback.rating
        ).all()
    )

    return render_template('professional_dashboard.html',professional=professional,upcoming_services=upcoming_services,closed_services=closed_services)

#pending professional dashboard
@app.route("/pending_approval")
def pending_approval():
    return render_template('pending_approval.html')

#professional accepts a service
@app.route('/accept_service/<int:service_id>', methods=['POST'])
def accept_service(service_id):
    service = ServiceRequest.query.get(service_id)
    if not service:
        return "Service not found.", 404
    
    if service.status != 'Requested':
        return "Service already processed.", 400

    service.status = 'Accepted'
    db.session.commit()

    professional = ProfessionalDetails.query.filter_by(id=service.professional_id).first()
    if not professional:
        return "Professional details not found.", 404

    return redirect(url_for('professional_dashboard', email=professional.email))

##professional rejects a service
@app.route('/reject_service/<int:service_id>', methods=['POST'])
def reject_service(service_id):
    service = ServiceRequest.query.get(service_id)
    if not service:
        return "Service not found.", 404
    
    if service.status != 'Requested':
        return "Service already processed.", 400

    service.status = 'Rejected'
    db.session.commit()

    professional = ProfessionalDetails.query.filter_by(id=service.professional_id).first()
    if not professional:
        return "Professional details not found.", 404

    return redirect(url_for('professional_dashboard', email=professional.email))

@app.route('/prof_search/<email>', methods=['GET', 'POST'])
def prof_search(email):
    professional = ProfessionalDetails.query.filter_by(email=email).first()
    if request.method == 'POST':
        search_date = request.form.get('search_query')
        services = ServiceRequest.query.filter(
            ServiceRequest.professional_id == professional.id,
            ServiceRequest.date_time.like(f"{search_date}%")
            ).all()
        service_data = []
        for service in services:
            customer = CustomerDetails.query.get(service.customer_id)
            feedback = Feedback.query.filter_by(request_id=service.id).first()
            rating = feedback.rating if feedback else None
            service_data.append({
                'service_id': service.id,
                'customer_name': customer.name,
                'location': service.address,
                'status': service.status,
                'rating': rating
            })
            return render_template('prof_search.html', service_data=service_data, professional=professional)
        else:
            return render_template('prof_search.html', message="No services assigned on this date", professional=professional)
    
    return render_template('prof_search.html', professional=professional)

@app.route("/admin_summary")
def admin_summary():
    generate_user_ratings_pie_chart()
    generate_service_requests_bar_chart()
    return render_template("admin_summary.html")

def generate_user_ratings_pie_chart():
    ratings_summary = get_user_ratings_summary()
    labels = list(ratings_summary.keys())
    sizes = list(ratings_summary.values())
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("User Ratings for Services")
    plt.savefig("./static/images/user_ratings_pie.jpeg")
    plt.clf()

def generate_service_requests_bar_chart():
    service_summary = get_service_requests_summary()
    services = list(service_summary.keys())
    counts = list(service_summary.values())
    plt.figure(figsize=(8, 6))
    plt.bar(services, counts, color="green", width=0.4)
    plt.title("Number of Requests per Service")
    plt.xlabel("Service")
    plt.ylabel("Number of Requests")
    plt.savefig("./static/images/service_requests_bar.jpeg")
    plt.clf()

def get_user_ratings_summary():
    # Query the Feedback table to count ratings grouped by their value
    ratings = db.session.query(
        Feedback.rating, 
        db.func.count(Feedback.rating)
    ).group_by(Feedback.rating).all()
    return {rating: count for rating, count in ratings}

def get_service_requests_summary():
    # Query the Service table via ServiceRequest to count requests grouped by service name
    services = db.session.query(
        Service.name, 
        db.func.count(ServiceRequest.id)
    ).join(Service, ServiceRequest.service_id == Service.id).group_by(Service.name).all()
    return {service_name: count for service_name, count in services}

@app.route("/professional_summary/<email>")
def professional_summary(email):
    professional = ProfessionalDetails.query.filter_by(email=email).first()

    if not professional:
        return "Professional not found", 404

    # Generate charts
    ratings_plot = generate_professional_ratings_summary(professional.id)
    ratings_plot.savefig("./static/images/prof_ratings_summary.jpeg")
    ratings_plot.clf()

    services_plot = generate_professional_services_summary(professional.id)
    services_plot.savefig("./static/images/prof_services_summary.jpeg")
    services_plot.clf()

    return render_template("professional_summary.html", professional=professional)


def generate_professional_ratings_summary(professional_id):
    ratings = db.session.query(
        Feedback.rating, 
        db.func.count(Feedback.rating)
    ).join(ServiceRequest, ServiceRequest.id == Feedback.request_id) \
      .filter(ServiceRequest.professional_id == professional_id, ServiceRequest.status == "Closed") \
      .group_by(Feedback.rating).all()

    # Format the results into a dictionary for easy use in the pie chart
    summary = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for rating, count in ratings:
        summary[rating] = count

    values = [summary[5], summary[4], summary[3], summary[2], summary[1]]
    labels = ['Excellent', 'Good', 'Average', 'Poor']
    labels = [label for label, value in zip(['Excellent', 'Good', 'Average', 'Poor'], values) if value > 0]
    values = [value for value in values if value > 0]
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    
    plt.title("User Ratings for Closed Services")
    return plt

def generate_professional_services_summary(professional_id):
    services = (
        ServiceRequest.query.filter_by(professional_id=professional_id)
        .with_entities(ServiceRequest.status, db.func.count(ServiceRequest.id))
        .group_by(ServiceRequest.status)
        .all()
    )
    
    # Debug: print the result of the query
    print(services)

    summary = {"Received": 0, "Accepted": 0, "Rejected": 0}

    for status, count in services:
        if status == "Pending":
            summary["Received"] += count
        elif status == "Accepted":
            summary["Accepted"] += count
        elif status == "Rejected":
            summary["Rejected"] += count
    
    labels = list(summary.keys())
    values = list(summary.values())

    if sum(values) > 0:
        plt.bar(labels, values, color=["blue", "green", "red"])
        plt.title("Service Status Summary")
        plt.xlabel("Status")
        plt.ylabel("Count")
    else:
        plt.bar(labels, [0]*len(labels), color=["blue", "green", "red"])  # Ensure bar chart has empty bars
        plt.title("No Data Available")

    return plt

@app.route("/user_summary/<email>")
def user_summary(email):
    user = CustomerDetails.query.filter_by(email=email).first()

    if not user:
        return "User not found", 404

    # Generate chart for service request status summary
    status_plot = generate_user_status_summary(user.id)
    status_plot.savefig("./static/images/user_status_summary.jpeg")
    status_plot.clf()

    return render_template("user_summary.html", user=user)

def generate_user_status_summary(user_id):
    statuses = (
        ServiceRequest.query.filter_by(user_id=user_id)
        .with_entities(ServiceRequest.status, db.func.count(ServiceRequest.id))
        .group_by(ServiceRequest.status)
        .filter(ServiceRequest.status.in_(['Requested', 'Closed']))  # Filter for only Requested and Closed
        .all()
    )

    # Create a dictionary for summary
    summary = {"Requested": 0, "Closed": 0}
    for status, count in statuses:
        if status == "Requested":
            summary["Requested"] = count
        elif status == "Closed":
            summary["Closed"] = count
    
    labels = list(summary.keys())
    values = list(summary.values())

    # Plot the bar chart
    plt.bar(labels, values, color=["blue", "red"])
    plt.title("Service Request Status Summary")
    plt.xlabel("Status")
    plt.ylabel("Count")
    
    return plt
