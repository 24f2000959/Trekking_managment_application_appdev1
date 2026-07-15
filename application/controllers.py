from flask import Flask, render_template, redirect, request, url_for, flash, session
from .decorators import admin_required, login_required, staff_required, user_required
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


from flask import current_app as app
# we cannot do somethign like this 
#                                 from .app import app
# because it creates circular importing error 
# we are importing app to controllers.py file and importing controller to app.py file .this cause circular import error
# so to concur this we do importing as form current_app as app

from .models import *


@app.route("/")
def landing_page():
    session.clear()
    trek = Trek.query.filter(Trek.end_date >= datetime.today().date()).all()
    return render_template("landing_page.html", trek=trek)

@app.route("/landing/search", methods=["GET"])
def landing_search():
    keyword = request.args.get("search")
    if not keyword:
        trek = Trek.query.filter(
                                    Trek.end_date >= datetime.today().date()
                                ).all()
    else:
        trek = Trek.query.filter(
                                  Trek.end_date >= datetime.today().date(),
                                  (Trek.trek_name.ilike(f"%{keyword}%"))
                                  ).all()
    return render_template("landing_page.html", trek=trek)
    

# =====================================================================================================================
# ===================================================signin=================================================================
# ===================================================================================================================
@app.route('/signin_page' ,methods=["GET","POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("name")
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        cpwd = request.form.get("cpwd")
        role = request.form.get("role")

        #validation
        if not username or not email or not pwd or not role:
            flash("fill all the required field")
            return redirect("/signin_page")
        if pwd != cpwd:
            flash("password and confirm password should be same")
            return redirect("/signin_page")
        
        #chechking existing user
        this_user = User.query.filter_by(user_name=username).first()
        if this_user:
            flash("username is takken")
            return redirect("/signin_page")
        
        this_user = User.query.filter_by(email=email).first()
        if this_user:
            flash("email is takken")
            return redirect("/signin_page")
        
        this_user = User.query.filter_by(user_name=username, email=email).first()
        if this_user:
            flash("already registered")
            return redirect("/signin_page")
        
        # staff should be approved by admin, but user already approve
        if role == "staff":
            status = "pending"
        else: 
            status = "approve"
        
        new_user = User(user_name=username,email=email,password=pwd,role=role,status=status)
        db.session.add(new_user)
        db.session.commit()

        if new_user.role == "staff":
            flash("registered success fully wait for to admin to approve you ")
            return redirect("/login_page")
        else: 
            flash("registration successfull")
            return redirect("/login_page")

    return render_template("signin_page.html")




# ====================================================================================================================
# ===================================================|lognin|=================================================================
#=======================================================================================================================
@app.route('/login_page',methods=["GET","POST"])
def login():
    if request.method == 'POST':
        email = request.form.get("email_id")
        pwd = request.form.get("pwd")

        if not email or not pwd:
            flash("Please fill all fields.")
            return redirect("/login_page")
        
        this_user = User.query.filter_by(email=email).first()
        if this_user is None:
            flash("first signin your account")
            return redirect("/login_page")
        
        if this_user.password != pwd:
            flash("Incorrect Password")
            return redirect("/login_page")
        
        if this_user.role == "staff" and this_user.status == "blacklist":
            flash("admin blacklisted your account")
            return redirect("/login_page")
        
        if this_user.role == "user" and this_user.status == "blacklist":
            flash("admin blacklisted your account")
            return redirect("/login_page")

        #storing info in sessions
        session["user_id"] = this_user.id
        session["role"] = this_user.role
        session["user_name"] = this_user.user_name
        session["user_email"] = this_user.email

        #admin
        if this_user.role == "admin":
            return redirect("/admin/admin_dashboard")
        
        #staff
        if this_user.role == "staff" and this_user.status == "approve":
            return redirect("/staff/staff_dashboard")
        if this_user.role== "staff" and this_user.status == "pending":
            flash("wait for admin to approve you")
            return redirect("/login_page")
        
        #user
        if this_user.role == "user" :
            return redirect("/user/user_dashboard")
            
    return render_template("login_page.html")



# ==========================================================================================================================
# ===================================================|admin|=================================================================
# ==============================================================================================================================
@app.route("/admin/admin_dashboard")
@login_required
@admin_required
def admin_dashboard():
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    pending_staff = User.query.filter_by(role="staff",status="pending").count()
    blacklist_staff = User.query.filter_by(role="staff",status="blacklist").count() 
    approve_staff = User.query.filter_by(role="staff",status="approve").count() 
    blacklist_user = User.query.filter_by(role="user",status="blacklist").count() 
    approve_user = User.query.filter_by(role="user",status="approve").count() 
    total_bookings = Booking.query.count()

    if Trek.query.count() <= 0 or User.query.filter_by(role="staff").count() <=0:
        return render_template("admin/admin_dashboard.html",
                                                            this_user=this_user,
                                                            total_treks=total_treks, 
                                                            total_users = total_users,
                                                            total_staff = total_staff,
                                                            pending_staff=pending_staff,
                                                            total_bookings=total_bookings,
                                                            approve_staff=approve_staff,
                                                            blacklist_staff=blacklist_staff,
                                                            approve_user=approve_user,
                                                            blacklist_user=blacklist_user,
                                                        )

    #barchart------------ 
    labels = ["Pending", "Approved", "Blacklisted"]
    sizes = [pending_staff, approve_staff, blacklist_staff]
    color = ["brown", "darkgreen", "orange"]
    
    plt.figure(figsize=(5,4))
    plt.bar(labels, sizes, color=color)
    # plt.yticks([])
    # plt.barh(labels, sizes, color=color)
    plt.title("Staff status")
    plt.savefig("static/images/admin_bar.png")
    plt.close()

    # pie chart------------------
    hard_trek_per = Trek.query.filter_by(difficulty="hard").count()
    moderate_trek_per = Trek.query.filter_by(difficulty="moderate").count()
    easy_trek_per = Trek.query.filter_by(difficulty="easy").count()
    labels = ["Moderate", "Easy", "Hard"]
    sizes = [moderate_trek_per, easy_trek_per, hard_trek_per]
    color = ["brown", "darkgreen", "orange"]

    plt.figure(figsize=(6,3))
    plt.pie(sizes,labels=labels, colors=color, autopct="%1.1f%%")
    plt.title("trek analytics")
    plt.savefig("static/images/admin_pie.png")
    plt.close()

    return render_template("admin/admin_dashboard.html",this_user=this_user,
                            total_treks=total_treks, 
                            total_users = total_users,
                            total_staff = total_staff,
                            pending_staff=pending_staff,
                            total_bookings=total_bookings,
                            approve_staff=approve_staff,
                            blacklist_staff=blacklist_staff,
                            approve_user=approve_user,
                            blacklist_user=blacklist_user,
                            hard_trek_per=hard_trek_per,
                            moderate_trek_per=moderate_trek_per,
                            easy_trek_per=easy_trek_per)


#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|bookings|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/bookings_page")
@login_required
@admin_required
def bookings_page():
    bookings=Booking.query.all()
    return render_template("/admin/bookings_page.html", bookings=bookings)


#XXXXXXXXXXXXXXXXXXXXXXXXXXXX|treks|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/treks_page")
@login_required
@admin_required
def treks_page():
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    treks=Trek.query.all()
    return render_template("/admin/treks_page.html", treks=treks, this_user=this_user)

# ----------------------|add trek|----------------------
@app.route("/admin/add_trek",methods=["GET","POST"])
@login_required
@admin_required
def add_trek():
    # method-POST
    if request.method =="POST":
        trek_name = request.form.get("trek_name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        total_slots = request.form.get("total_slots")

        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        duration = (end_date-start_date).days
        staff_id = request.form.get("staff_id")
        description = request.form.get("description")
        status = request.form.get("status")
        # checking conditions
        if not trek_name or not location or not difficulty or not duration or  not total_slots or not start_date or not end_date or not description or not status or not staff_id:
            flash("fill all fields")
            return redirect("/admin/add_trek")
        
        existing_staff = Trek.query.filter(
                                                Trek.staff_id == staff_id,
                                                Trek.status == "open",
                                                Trek.start_date <= end_date,
                                                Trek.end_date >= start_date
                                            ).first()
        if existing_staff:
            flash("staff is already assigned to another trek")
            return redirect("/admin/add_trek")
        
        existing_trek = Trek.query.filter_by(trek_name=trek_name,start_date=start_date).first()
        if existing_trek:
            flash("A trek with the same name and start date already exists.")
            return redirect("/admin/add_trek")
        
        if start_date <= datetime.today().date():
            flash("trek starting date must be greater than todays date")
            return redirect("/admin/add_trek")
        
        if start_date >= end_date:
            flash("startdate should be less than enddate")
            return redirect("/admin/add_trek")
    
        if int(total_slots) <= 0:
            flash("total slots must be greater than 0")
            return redirect("/admin/add_trek")
        # adding to database    
        new_trek = Trek(
                            trek_name=trek_name,
                            location=location,
                            difficulty=difficulty,
                            duration=int(duration),
                            total_slots=int(total_slots),
                            available_slots=int(total_slots),
                            start_date=start_date,
                            end_date=end_date,
                            description=description,
                            status=status,
                            staff_id=staff_id
                        )
        db.session.add(new_trek)
        db.session.commit()
        return redirect("/admin/treks_page")
    # method-GET
    staffs = User.query.filter_by(role="staff",status="approve").all()
    return render_template("/admin/add_trek.html",staffs=staffs)
    


#-----------|edit trek|----------------------
@app.route("/admin/edit_trek/<int:trek_id>", methods=["GET","POST"])
@login_required
@admin_required
def edit_trek(trek_id):
    
    treks = Trek.query.filter_by(id=trek_id).first()
    if treks is None:
        flash("trek not find")
        return redirect("/admin/treks_page")
    
    if treks.end_date < datetime.today().date():
        flash("completed treks cannot be edited")
        return redirect("/admin/treks_page")
    
    staffs = User.query.filter_by(role="staff",status="approve").all()
    # method-POST
    if request.method == "POST":
        trek_name = request.form.get("trek_name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        total_slots = request.form.get("total_slots")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        description = request.form.get("description")
        status = request.form.get("status")
        staff_id = request.form.get("staff_id")
        # check all fileds are filled or not
        if not trek_name or not location or not difficulty or  not total_slots or not start_date or not end_date or not description or not status or not staff_id:
            flash("fill all fields")
            return redirect(f"/admin/edit_trek/{trek_id}")

        # updating value 
        treks.trek_name = trek_name
        treks.location = location
        treks.difficulty = difficulty

        new_total_slots = int(total_slots)
        booked_slots = treks.total_slots - treks.available_slots
        if new_total_slots < booked_slots:
            flash(f"At least {booked_slots} slots are required because users have already booked.")
            return redirect(f"/admin/edit_trek/{trek_id}")
        treks.total_slots = new_total_slots
        treks.available_slots = new_total_slots - booked_slots

        
        start_date = datetime.strptime(start_date,"%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        if start_date >= end_date:
            flash("Start date must be before the end date.")
            return redirect(f"/admin/edit_trek/{trek_id}")
        treks.start_date = start_date
        treks.end_date = end_date
        
        treks.duration = (end_date - start_date).days
        treks.staff_id = int(staff_id)
        treks.description = description
        treks.status = status
    
        # checking conditions
        existing_staff = Trek.query.filter(
                                                Trek.staff_id == treks.staff_id,
                                                Trek.status == "open",
                                                Trek.end_date >= datetime.today().date(),
                                                Trek.id != trek_id
                                           ).first()
        if existing_staff:
            flash("This staff is already assigned to another open trek.")
            return redirect(f"/admin/edit_trek/{trek_id}")

        if int(treks.duration) <= 0:
            flash("Duration must be greater than 0")
            return redirect(f"/admin/edit_trek/{trek_id}")

        if int(treks.total_slots) <= 0:
            flash("Total slots must be greater than 0")
            return redirect(f"/admin/edit_trek/{trek_id}")
        
        duplicate = Trek.query.filter(
                                        Trek.trek_name == treks.trek_name,
                                        Trek.start_date == treks.start_date,
                                        Trek.id != treks.id
                                    ).first()
        if duplicate:
            flash("another trek with the same name and start date already exists.")
            return redirect(f"/admin/edit_trek/{trek_id}")
        #updating data base
        db.session.commit()
        flash("edit successfull")
        return redirect("/admin/treks_page")
    # method-GET
    return render_template("/admin/edit_trek.html",staffs=staffs,treks=treks)

#-----------------|delete trek|------------------
@app.route("/admin/delete_trek/<int:trek_id>")
@login_required
@admin_required
def delete_edit(trek_id):
        
    trek = Trek.query.filter_by(id=trek_id).first()
    if trek is None:
        flash("trek not found")
        return redirect("/admin/treks_page")
    
    if Booking.query.filter_by(trek_id=trek.id).first():
        flash("cannot delete trek because bookings exist.")
        return redirect("/admin/treks_page")
    
    db.session.delete(trek)
    db.session.commit()
    flash("trek deleted successfully")

    return redirect("/admin/treks_page")

# -------------------|search treks|----------------------------------
@app.route("/admin/admin_search_trek" ,methods=["GET"])
@login_required
@admin_required
def admin_search_trek():
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    
    keyword = request.args.get("search","").strip()
    if not keyword:
        return redirect("/admin/treks_page")
    treks = Trek.query.filter(
                              (Trek.trek_name.ilike(f"%{keyword}%"))|
                               (Trek.location.ilike(f"%{keyword}%"))
                              ).all()
    
    return render_template("/admin/treks_page.html",treks=treks,this_user=this_user)


#XXXXXXXXXXXXXxxxxxxxxxx|staff|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/staff_page")
@login_required
@admin_required
def staff_page():
     
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    staffs = User.query.filter_by(role="staff").all()

    return render_template("/admin/staff_page.html", staffs=staffs, this_user=this_user)


# ------------------|approve staff|------------------------------
@app.route("/admin/approve_staff/<int:staff_id>")
@login_required
@admin_required
def approve_staff(staff_id):
    
    staff = User.query.filter_by(id=staff_id,role="staff").first()
    if staff is None:
       return redirect("/admin/staff_page")
    if staff:
        staff.status = "approve"
        db.session.commit()

    return redirect("/admin/staff_page")


# --------------------|balcklist staff|---------------
@app.route("/admin/blacklist_staff/<int:staff_id>")
@login_required
@admin_required
def blacklist_staff(staff_id):

    staff = User.query.filter_by(id=staff_id).first()
    if staff is None:
        flash("staff is not there")
        return redirect("/admin/staff_page")
    
    assigned_trek = Trek.query.filter(
                                        Trek.staff_id == staff.id, 
                                        Trek.status == "open",
                                          Trek.end_date >= datetime.today().date()
                                    ).first()
    if assigned_trek:
        flash("Cannot blacklist staff assigned to an active trek.")
        return redirect("/admin/staff_page")
    
    staff=User.query.filter_by(id=staff_id,role="staff").first()
    if staff is None:
        return redirect("/admin/staff_page")
    if staff:
        staff.status = "blacklist"
        db.session.commit()

    return redirect("/admin/staff_page")

# ---------------|search staff|----------------------
@app.route("/admin/admin_search_staff", methods=["GET"])
@login_required
@admin_required
def admin_search_staff():
    
    keyword = request.args.get("search","").strip()
    if not keyword:
        return redirect("/admin/staff_page")
    
    staffs=User.query.filter(
                            User.role == "staff",
                            (User.user_name.ilike(f"%{keyword}%"))
                            ).all()
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    return render_template("/admin/staff_page.html", staffs=staffs, this_user=this_user)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|user|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/user_page")
@login_required
@admin_required
def user_page():
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    users = User.query.filter_by(role="user").all()

    return render_template("/admin/user_page.html",users=users, this_user=this_user)


#----------------|approve user|------------------------
@app.route("/admin/approve_user/<int:user_id>")
@login_required
@admin_required
def approve_user(user_id):
    
    user = User.query.filter_by(id=user_id,role="user").first()
    if user is None:
        return redirect("/admin/user_page")
    if user:
        user.status = "approve"
        db.session.commit()

    return redirect("/admin/user_page")

#----------|blacklist user|----------------
@app.route("/admin/blacklist_user/<int:user_id>")
@login_required
@admin_required
def blacklist_user(user_id):
    
    user = User.query.filter_by(id=user_id,role="user").first()
    if user is None:
        return redirect("/admin/user_page")
    if user:
        user.status = "blacklist"
        db.session.commit()

    return redirect("/admin/user_page")

# ----------------|search user|--------------------------
@app.route("/admin/admin_search_user")
@login_required
@admin_required
def admin_search_user():
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    
    keyword=request.args.get("search","").strip()
    if not keyword:
        return redirect("/admin/user_page")
    users=User.query.filter(
                            User.role == "user",
                            (User.user_name.ilike(f"%{keyword}%"))
                            ).all()
    
    return render_template("/admin/user_page.html",users=users, this_user=this_user)







# ==========================================================================================================================
# ===================================================|User|=================================================================
# =========================================================================================================================
@app.route("/user/user_dashboard")
@login_required
@user_required
def user_dashboard():
    
    this_user = User.query.filter_by(id=session["user_id"]).first()
    
    treks = Trek.query.filter_by(status="open").count()
    user_bookings = Booking.query.filter_by(user_id=this_user.id,booking_status="booked").count()

    # graph
    easy = Trek.query.filter_by(difficulty="easy").count()
    hard = Trek.query.filter_by(difficulty="hard").count()
    moderate = Trek.query.filter_by(difficulty="moderate").count()
    labels = ["easy", "moderate", "hard"]
    sizes = [easy, moderate, hard]
    color = ["brown", "darkgreen", "orange"]

    plt.figure(figsize=(12, 5))
    plt.barh(labels, sizes, color=color)
    plt.title("Difficulty of number of treks")
    plt.savefig("static/images/user_bar.png")
    plt.close()

    return render_template("/user/user_dashboard.html", this_user=this_user, treks=treks, user_bookings=user_bookings)

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|profile page|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/user/user_profile_page")
@login_required
@user_required
def user_profile_page():

    this_user=User.query.filter_by(id=session.get("user_id")).first()
    
    return render_template("/user/profile_page.html" , this_user=this_user)

# ----------------------|edit profle|-----------------------------
@app.route("/user/user_edit_profile/<int:u_id>" ,methods=["GET", "POST"])
@login_required
@user_required
def user_edit_profile(u_id):

    this_user = User.query.filter_by(id=session.get("user_id")).first()
    # method-POST
    if request.method=="POST":
        new_password = request.form.get("password", "").strip()
        if not new_password:
            flash("Please enter a password.")
            return redirect(f"/user/user_edit_profile/{u_id}")

        this_user.password = new_password
        db.session.commit()

        return redirect("/user/user_profile_page")
    # mthod-GET
    return render_template("/user/edit_profile.html", this_user=this_user)

#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|trek page|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/user/trek_page")
@login_required
@user_required
def trek_page():
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    trek = Trek.query.filter(
                                Trek.status == "open",
                                Trek.end_date >= datetime.today().date()
                            ).all()

    return render_template("/user/treks_page.html" ,trek=trek)

# ------------- trek info ---------------------
@app.route("/user/trek_info/<int:trek_id>")
@login_required
@user_required
def trek_info(trek_id):
    
    trek=Trek.query.filter_by(id=trek_id).first()
    if trek is None:
        flash("trek is not there")
        return redirect("/user/trek_page")
    
    return render_template("/user/trek_info.html",trek=trek)

#---------trek booking-------------
@app.route("/user/trek_book/<int:trek_id>")
@login_required
@user_required
def trek_book(trek_id):
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    
    trek=Trek.query.filter_by(id=trek_id).first()
    if trek is None:
        flash("trek is not there")
        return redirect("/user/trek_page")
    if trek.status != "open":
        flash("thsi trek is not open")
        return redirect("/user/trek_page")
    if trek.available_slots <= 0 :
        flash("no slots available")
        return redirect("/user/trek_page")
    if trek.end_date < datetime.today().date():
        flash("This trek has already ended.")
        return redirect("/user/trek_page")
    
    booking = Booking.query.filter_by(user_id=this_user.id, trek_id=trek.id,booking_status="booked").first()
    if booking:
        flash("already registered for this trek")
        return redirect("/user/trek_page")
    # creating database
    new_booking = Booking(user_id=this_user.id, trek_id=trek.id, booking_status="booked")
    db.session.add(new_booking)
    trek.available_slots -= 1
    db.session.commit()
    flash("trek booked successfully")

    return redirect("/user/trek_page")

# ------------------------|search trek|--------------------
@app.route("/user/user_search_trek", methods=["GET"])
@login_required
@user_required
def user_search_trek():
        
    keyword=request.args.get("search","").strip()
    if not keyword:
        return redirect("/user/trek_page")
    trek = Trek.query.filter(
                                Trek.status == "open",
                                Trek.end_date >= datetime.today().date(),
                                (
                                    (Trek.trek_name.ilike(f"%{keyword}%")) |
                                    (Trek.location.ilike(f"%{keyword}%")) |
                                    (Trek.difficulty.ilike(f"%{keyword}%"))
                                )
                            ).all()
    return render_template("/user/treks_page.html" ,trek=trek)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX bookings XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx
@app.route("/user/booking_history")
@login_required
@user_required
def booking_history():
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    booking= Booking.query.filter_by(user_id=this_user.id).all()

    return render_template("/user/booking_history.html", booking=booking)

# ----cancel booking----
@app.route("/user/cancel_booking/<int:booking_id>")
@login_required
@user_required
def cancel_booking(booking_id):
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    
    booking = Booking.query.filter_by(id=booking_id,user_id=this_user.id,booking_status="booked").first()
    if booking is None:
        flash("this booking is not existed")
        return redirect("/user/booking_history")
    if booking.trek.start_date <= datetime.today().date():
        flash("Booking cannot be cancelled after the trek has started.")
        return redirect("/user/booking_history")
    if booking.booking_status == "cancel":
        flash("booking already canceled")
        return redirect("/user/booking_history")
    # creating database
    booking.booking_status = "cancel"
    booking.trek.available_slots += 1
    db.session.commit()
    flash("booking cancelled")

    return redirect("/user/booking_history")







# ============================================================================================================================
# =================================================== |staff|=================================================================
# =============================================================================================================================
@app.route("/staff/staff_dashboard")
@login_required
@staff_required
def staff_dashboard():

    this_user = User.query.filter_by(id=session.get("user_id")).first()
    
    trek = Trek.query.filter(
                                Trek.staff_id == this_user.id,
                                Trek.end_date >= datetime.today().date()
                            ).count()

    assigned_treks = Trek.query.filter_by(staff_id=this_user.id).all()

    total_participants = 0
    trek_names=[]
    participants=[]
    for trek in assigned_treks:
        booked = Booking.query.filter_by(trek_id=trek.id,booking_status="booked").count()
        total_participants += booked
        trek_names.append(trek.trek_name)
        participants.append(booked)
    # graph
    labels = trek_names
    sizes = participants

    plt.figure(figsize=(11,6))
    plt.barh(labels, sizes)
    plt.title("Trekkers on each treks")
    plt.savefig("static/images/staff_bar_1.png")
    plt.close()
   
    return render_template("staff/staff_dashboard.html", this_user=this_user,trek=trek, total_participants=total_participants )


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|profile page|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/staff/staff_profile_page")
@login_required
@staff_required
def staff_profile_page():
    
    this_user=User.query.filter_by(id=session.get("user_id")).first()
    
    return render_template("/staff/profile_page.html" , this_user=this_user)

# ----------------------|edit profle|-----------------------------
@app.route("/staff/staff_edit_profile/<int:s_id>" ,methods=["GET", "POST"])
@login_required
@staff_required
def staff_edit_profile(s_id):
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    # method-POST
    if request.method=="POST":
        new_password = request.form.get("password", "").strip()
        if not new_password:
            flash("Please enter a password.")
            return redirect(f"/staff/staff_edit_profile/{s_id}")
        this_user.password = new_password
        # databse creation
        db.session.commit()
        return redirect("/staff/staff_profile_page")
    # method-GET
    return render_template("/staff/edit_profile.html", this_user=this_user)


# XXXXXXXXXXXXXXXXXXXXXXxxxxx|my trek|XXXXXXXXXXXXXXXXXXXXXXX
@app.route("/staff/my_treks_page")
@login_required
@staff_required
def my_treks_page():
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()
    trek = Trek.query.filter_by(staff_id=this_user.id).all()
    
    return render_template("/staff/my_treks_page.html",this_user=this_user, trek=trek)

# ---------------------|trekker|---------------
@app.route("/staff/trekker_page/<int:t_id>")
@login_required
@staff_required
def trekker_page(t_id):
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()
    
    trek = Trek.query.filter_by(id=t_id,staff_id=this_user.id).first()
    if trek is None:
        flash("Trek not found")
        return redirect("/staff/my_treks_page")
    
    booking = Booking.query.filter_by(trek_id=trek.id,booking_status="booked").all()

    return render_template("/staff/trekker_page.html",this_user=this_user, trek=trek, booking=booking)

# ---------------|edit treks|---------------------------
@app.route("/staff/trek_edit/<int:t_id>", methods=["GET","POST"])
@login_required
@staff_required
def trek_edit(t_id):
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()
    
    trek = Trek.query.filter_by(id=t_id, staff_id=this_user.id).first()
    if trek is None:
        flash("Trek not found")
        return redirect("/staff/my_treks_page")
    if trek.end_date < datetime.today().date():
        flash("Completed treks cannot be edited.")
        return redirect("/staff/my_treks_page")
    # method-POST
    if request.method=="POST":
        status = request.form.get("status")
        available_slot = request.form.get("available_slots")

        if not status or not available_slot:
            flash("please fill all fields")
            return redirect(f"/staff/trek_edit/{trek.id}")
        
        available_slot = int(available_slot)
        if available_slot < 0 :
            flash("available slots cannot be negative")
            return redirect(f"/staff/trek_edit/{trek.id}")
        if available_slot > trek.total_slots :
            flash("available slots cannot exceede total slots")
            return redirect(f"/staff/trek_edit/{trek.id}")
        
        booked = Booking.query.filter_by(trek_id=trek.id,booking_status="booked").count()
        if booked > 0 and status == "close":
            flash("You cannot close a trek while participants are still booked.")
            return redirect(f"/staff/trek_edit/{trek.id}")
        
        trek.status = status
        booked = Booking.query.filter_by(trek_id=trek.id, booking_status="booked").count()
        # updating database
        trek.available_slots = trek.total_slots - booked
        db.session.commit()
        flash("Trek updated successfully.")
        return redirect("/staff/my_treks_page")

    return render_template("/staff/trek_edit.html",this_user=this_user, trek=trek)






# ===========================================================================================================================
# ===================================================|logout|=================================================================
# =========================================================================================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")