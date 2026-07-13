from flask import Flask, render_template, redirect, request, url_for, flash, session
from datetime import datetime

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
    return render_template("landing_page.html")


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
        this_user = User.query.filter_by(email=email).first()
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

        if role == "staff":
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
def admin_dashboard():
    if "user_id" not in session:
        flash("login first!")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user_id = session.get("user_id")
    this_user = User.query.filter_by(id=user_id).first()

    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    pending_staff = User.query.filter_by(role="staff",status="pending").count()
    total_bookings = Booking.query.count()

    return render_template("admin/admin_dashboard.html",this_user=this_user,
                            total_treks=total_treks, 
                            total_users = total_users,
                            total_staff = total_staff,
                            pending_staff=pending_staff,
                            total_bookings=total_bookings)


#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|bookings|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/bookings_page")
def bookings_page():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthoried Access")
        return redirect("/login_page")

    this_user = User.query.filter_by(id=session.get("user_id"),role="admin").first()
    if this_user is None:
        flash("please login again ")
        return redirect("/login_page")
    
    bookings=Booking.query.all()

    return render_template("/admin/bookings_page.html", bookings=bookings)


#XXXXXXXXXXXXXXXXXXXXXXXXXXXX|treks|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/treks_page")
def treks_page():

    if "user_id" not in session:
        flash("login first!")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    treks=Trek.query.all()
    return render_template("/admin/treks_page.html", treks=treks, this_user=this_user)

# ----------------------|add trek|----------------------
@app.route("/admin/add_trek",methods=["GET","POST"])
def add_trek():
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login agian")
        return redirect("/login_page")

    if request.method =="POST":
        trek_name = request.form.get("trek_name")
        location = request.form.get("location")
        difficulty = request.form.get("difficulty")
        duration = request.form.get("duration")
        total_slots = request.form.get("total_slots")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        staff_id = request.form.get("staff_id")
        description = request.form.get("description")
        status = request.form.get("status")

        if not trek_name or not location or not difficulty or not duration or  not total_slots or not start_date or not end_date or not description or not status or not staff_id:
            flash("fill all fields")
            return redirect("/admin/add_trek")
        
        existing_staff = Trek.query.filter_by(staff_id=staff_id,status="open").first()
        if existing_staff:
            flash("staff is already assigned to another trek")
            return redirect("/admin/add_trek")
        
        existing_trek = Trek.query.filter_by(trek_name=trek_name,start_date=start_date).first()
        if existing_trek:
            flash("A trek with the same name and start date already exists.")
            return redirect("/admin/add_trek")
        
        if int(total_slots) <= 0:
            flash("total slots must be greater than 0")
            return redirect("/admin/add_trek")
        
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        if start_date >= end_date:
            flash("startdate should be less than enddate")
            return redirect("/admin/add_trek")
        
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
    
    staffs = User.query.filter_by(role="staff",status="approve").all()
    return render_template("/admin/add_trek.html",staffs=staffs)
    


#-----------|edit trek|----------------------
@app.route("/admin/edit_trek/<int:trek_id>", methods=["GET","POST"])
def edit_trek(trek_id):
    
    if "user_id" not in session:
        flash("Login first")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(role="admin",id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login first")
        return redirect("/login_page")
    
    treks = Trek.query.filter_by(id=trek_id).first()
    if treks is None:
        flash("trek not find")
        return redirect("/admin/treks_page")
    
    staff = User.query.filter_by(role="staff",status="approve").all()
    
    if request.method == "POST":
        treks.trek_name = request.form.get("trek_name")
        treks.location = request.form.get("location")
        treks.difficulty = request.form.get("difficulty")
        treks.duration = request.form.get("duration")
        treks.total_slots = request.form.get("total_slots")
        treks.start_date = datetime.strptime(request.form.get("start_date"),"%Y-%m-%d").date()
        treks.end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()
        treks.staff_id = request.form.get("staff_id")
        treks.description = request.form.get("description")
        treks.status = request.form.get("status")

        existing_staff = Trek.query.filter(Trek.staff_id == treks.staff_id,Trek.status == "open",Trek.id != trek_id).first()
        if existing_staff:
            flash("This staff is already assigned to another open trek.")
            return redirect(f"/admin/edit_trek/{trek_id}")

        if datetime.strptime(request.form.get("start_date"),"%Y-%m-%d").date() > datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date():
            flash("start date should be less than end date")
            return redirect("/admin/treks_page")

        if int(treks.duration) <= 0:
            flash("Duration must be greater than 0")
            return redirect(f"/admin/edit_trek/{trek_id}")

        if int(treks.total_slots) <= 0:
            flash("Total slots must be greater than 0")
            return redirect(f"/admin/edit_trek/{trek_id}")

        db.session.commit()
        flash("edit successfull")
        return redirect("/admin/treks_page")
    
    staffs = User.query.filter_by(role="staff",status="approve").all()
    return render_template("/admin/edit_trek.html",staffs=staffs,treks=treks)

#-----------------|delete trek|------------------
@app.route("/admin/delete_trek/<int:trek_id>")
def delete_edit(trek_id):
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(role="admin", id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    trek = Trek.query.filter_by(id=trek_id).first()
    if trek is None:
        flash("trek not found")
        return redirect("/admin/treks_page")
    
    if Booking.query.filter_by(trek_id=trek.id).first():
        flash("Cannot delete trek because bookings exist.")
        return redirect("/admin/treks_page")
    
    db.session.delete(trek)
    db.session.commit()
    flash("trek deleted successfully")

    return redirect("/admin/treks_page")

# -------------------|search treks|----------------------------------
@app.route("/admin/admin_search_trek" ,methods=["GET"])
def admin_search_trek():
    if "user_id" not in session:
        flash("Please login first")
        return redirect("/login_page")

    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")

    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("Please login again")
        return redirect("/login_page")
    
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
def staff_page():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access!")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    staffs = User.query.filter_by(role="staff").all()
    return render_template("/admin/staff_page.html", staffs=staffs, this_user=this_user)


# ------------------|approve staff|------------------------------
@app.route("/admin/approve_staff/<int:staff_id>")
def approve_staff(staff_id):
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")

    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")

    staff = User.query.filter_by(id=staff_id,role="staff").first()
    if staff is None:
       return redirect("/admin/staff_page")

    if staff:
        staff.status = "approve"
        db.session.commit()
    return redirect("/admin/staff_page")


# --------------------|balcklist staff|---------------
@app.route("/admin/blacklist_staff/<int:staff_id>")
def blacklist_staff(staff_id):
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    staff=User.query.filter_by(id=staff_id,role="staff").first()
    if staff is None:
        return redirect("/admin/staff_page")
    if staff:
        staff.status = "blacklist"
        db.session.commit()
    return redirect("/admin/staff_page")

# ---------------|search staff|----------------------
@app.route("/admin/admin_search_staff", methods=["GET"])
def admin_search_staff():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access!")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    keyword = request.args.get("search","").strip()
    staffs=User.query.filter(
                              User.role =="staff",
                              (User.user_name.ilike(f"%{keyword}%"))
                            ).all()
    return render_template("/admin/staff_page.html", staffs=staffs, this_user=this_user)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|user|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/admin/user_page")
def user_page():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    users = User.query.filter_by(role="user").all()
    return render_template("/admin/user_page.html",users=users, this_user=this_user)


#----------------|approve user|------------------------
@app.route("/admin/approve_user/<int:user_id>")
def approve_user(user_id):
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user = User.query.filter_by(id=user_id,role="user").first()
    if user is None:
        return redirect("/admin/user_page")
    if user:
        user.status = "approve"
        db.session.commit()
    return redirect("/admin/user_page")

#----------|blacklist user|----------------
@app.route("/admin/blacklist_user/<int:user_id>")
def blacklist_user(user_id):
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")
    
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user = User.query.filter_by(id=user_id,role="user").first()
    if user is None:
        return redirect("/admin/user_page")
    if user:
        user.status = "blacklist"
        db.session.commit()
    return redirect("/admin/user_page")

# ----------------|search user|--------------------------
@app.route("/admin/admin_search_user")
def admin_search_user():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    if session.get("role") != "admin":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    keyword=request.args.get("search","").strip()
    users=User.query.filter(
                            User.role == "user",
                            (User.user_name.ilike(f"%{keyword}%"))
                            ).all()
    return render_template("/admin/user_page.html",users=users, this_user=this_user)







# ==========================================================================================================================
# ===================================================|User|=================================================================
# =========================================================================================================================
@app.route("/user/user_dashboard")
def user_dashboard():
    if "user_id" not in session:
        flash("login first!")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user_id = session.get("user_id")
    this_user = User.query.filter_by(id=user_id).first()
    if this_user is None : 
        session.clear()
        flash("please login again!")
        return redirect("/login_page")
    
    treks = Trek.query.filter_by(status="open").all()
    user_bookings = Booking.query.filter_by(user_id=this_user.id,booking_status="booked").all()
    return render_template("/user/user_dashboard.html", this_user=this_user, treks=treks, user_bookings=user_bookings)

# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|profile page|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/user/user_profile_page")
def user_profile_page():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user=User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    return render_template("/user/profile_page.html" , this_user=this_user)

# ----------------------|edit profle|-----------------------------
@app.route("/user/user_edit_profile/<int:u_id>" ,methods=["GET", "POST"])
def user_edit_profile(u_id):
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    if request.method=="POST":
        this_user.password = request.form.get("password")

        if not this_user.password:
            flash("please fill all the required fields")
            return redirect(f"/user/user_edit_profile/{u_id}")
        
        db.session.commit()
        return redirect("/user/user_profile_page")

    return render_template("/user/edit_profile.html", this_user=this_user)

#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|trek page|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/user/trek_page")
def trek_page():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
        
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    trek = Trek.query.filter_by(status="open").all()
    return render_template("/user/treks_page.html" ,trek=trek)

# ------------- trek info ---------------------
@app.route("/user/trek_info/<int:trek_id>")
def trek_info(trek_id):
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user=User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None : 
        flash("please login again")
        return redirect("/login_page")
    
    trek=Trek.query.filter_by(id=trek_id).first()
    if trek is None:
        flash("trek is not there")
        return redirect("/user/trek_page")
    return render_template("/user/trek_info.html",trek=trek)

#---------trek booking-------------
@app.route("/user/trek_book/<int:trek_id>")
def trek_book(trek_id):
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        flash("please login again")
        return redirect("/login_page")
    
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
    
    booking = Booking.query.filter_by(user_id=this_user.id, trek_id=trek.id,booking_status="booked").first()
    if booking:
        flash("already registered for this trek")
        return redirect("/user/trek_page")
    
    new_booking = Booking(user_id=this_user.id, trek_id=trek.id, booking_status="booked")
    db.session.add(new_booking)
    trek.available_slots -= 1
    db.session.commit()
    flash("trek booked successfully")
    return redirect("/user/trek_page")

# ------------------------|search trek|--------------------
@app.route("/user/user_search_trek", methods=["GET"])
def user_search_trek():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        flash("please login again")
        return redirect("/login_page")
    
    keyword=request.args.get("search","").strip()
    trek=Trek.query.filter(
                            (Trek.difficulty.ilike(f"%{keyword}%"))|
                            (Trek.location.ilike(f"%{keyword}%"))
                            ).all()
    return render_template("/user/treks_page.html" ,trek=trek)


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX bookings XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx
@app.route("/user/booking_history")
def booking_history():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized Access")
        return redirect("/login_page")

    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        flash("please login again")
        return redirect("/login_page")

    booking= Booking.query.filter_by(user_id=this_user.id).all()
    return render_template("/user/booking_history.html", booking=booking)

# ----cancel booking----
@app.route("/user/cancel_booking/<int:booking_id>")
def cancel_booking(booking_id):
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "user":
        flash("Unauthorized access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        flash("please login again")
        return redirect("/login_page")
    
    booking = Booking.query.filter_by(id=booking_id,user_id=this_user.id,booking_status="booked").first()
    if booking is None:
        flash("this booking is not existed")
        return redirect("/user/booking_history")
    if booking.booking_status == "cancel":
        flash("booking already canceled")
        return redirect("/user/booking_history")
    booking.booking_status = "cancel"
    booking.trek.available_slots += 1
    db.session.commit()
    flash("booking cancelled")

    return redirect("/user/booking_history")







# ============================================================================================================================
# =================================================== |staff|=================================================================
# =============================================================================================================================
@app.route("/staff/staff_dashboard")
def staff_dashboard():

    if "user_id" not in session:
        flash("login first !")
        return redirect("/login_page")

    if session.get("role") != "staff":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()

    if this_user is None :
        session.clear()   
        flash("first login")
        return redirect("login_page")
    
   
    return render_template("staff/staff_dashboard.html", this_user=this_user, )


# XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|profile page|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
@app.route("/staff/staff_profile_page")
def staff_profile_page():
    if "user_id" not in session:
        flash("login first")
        return redirect("/login_page")
    
    if session.get("role") != "staff":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user=User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    return render_template("/staff/profile_page.html" , this_user=this_user)

# ----------------------|edit profle|-----------------------------
@app.route("/staff/staff_edit_profile/<int:s_id>" ,methods=["GET", "POST"])
def staff_edit_profile(s_id):
    if "user_id" not in session:
        flash("first login")
        return redirect("/login_page")
    
    if session.get("role") != "staff":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    this_user = User.query.filter_by(id=session.get("user_id")).first()
    if this_user is None:
        session.clear()
        flash("please login again")
        return redirect("/login_page")
    
    if request.method=="POST":
        this_user.password = request.form.get("password")

        if not this_user.password:
            flash("please fill all the required fields")
            return redirect(f"/staff/staff_edit_profile/{s_id}")
        

        db.session.commit()
        return redirect("/staff/staff_profile_page")

    return render_template("/staff/edit_profile.html", this_user=this_user)


# XXXXXXXXXXXXXXXXXXXXXXxxxxx|my trek|XXXXXXXXXXXXXXXXXXXXXXX
@app.route("/staff/my_treks_page")
def my_treks_page():
    if "user_id" not in session:
        flash("login first !")
        return redirect("/login_page")

    if session.get("role") != "staff":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()

    if this_user is None :
        session.clear()   
        flash("first login")
        return redirect("login_page")
    
    trek = Trek.query.filter_by(staff_id=this_user.id).all()
    
    return render_template("/staff/my_treks_page.html",this_user=this_user, trek=trek)

# ---------------------|trekker|---------------
@app.route("/staff/trekker_page/<int:t_id>")
def trekker_page(t_id):
    if "user_id" not in session:
        flash("login first !")
        return redirect("/login_page")

    if session.get("role") != "staff":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()

    if this_user is None :
        session.clear()   
        flash("first login")
        return redirect("login_page")
    
    trek = Trek.query.filter_by(id=t_id,staff_id=this_user.id).first()
    if trek is None:
        flash("Trek not found")
        return redirect("/staff/my_treks_page")
    
    booking = Booking.query.filter_by(trek_id=trek.id,booking_status="booked").all()
    return render_template("/staff/trekker_page.html",this_user=this_user, trek=trek, booking=booking)

# ---------------|edit treks|---------------------------
@app.route("/staff/trek_edit/<int:t_id>", methods=["GET","POST"])
def trek_edit(t_id):
    if "user_id" not in session:
        flash("login first !")
        return redirect("/login_page")

    if session.get("role") != "staff":
        flash("Unauthorized Access")
        return redirect("/login_page")
    
    user_id = session.get("user_id")  
    this_user = User.query.filter_by(id=user_id).first()

    if this_user is None :
        session.clear()   
        flash("first login")
        return redirect("login_page")
    
    trek = Trek.query.filter_by(id=t_id, staff_id=this_user.id).first()
    if trek is None:
        flash("Trek not found")
        return redirect("/staff/my_treks_page")
    
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
        
        trek.status = status
        trek.available_slots = available_slot
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