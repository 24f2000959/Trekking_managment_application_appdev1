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

# ===================================================signin=================================================================

@app.route('/signin_page' ,methods=["GET","POST"])
def signin():
    if request.method == "POST":

        username = request.form.get("name")
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        role = request.form.get("role")

        #validation
        if not username or not email or not pwd or not role:
            flash("fill all the required field")
            return redirect("/signin_page")
        
        #chechking existing user
        this_user = User.query.filter_by(email=email).first()
        if this_user:
            flash("already registered")
            return redirect("/signin_page")
        
        # staff should be approved by admin but user already approved
        if role == "staff":
            status = "pending"
        else: 
            status = "approved"
        
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


# ===================================================lognin=================================================================

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
        
        if this_user.role == "staff" and this_user.status == "blacklisted":
            flash("admin blacklisted your account")

        #storing info in sessions
        session["user_id"] = this_user.id
        session["role"] = this_user.role
        session["user_name"] = this_user.user_name
        session["user_email"] = this_user.email

        #admin
        if this_user.role == "admin":
            return redirect("/admin/admin_dashboard")
        
        #staff
        if this_user.role == "staff" and this_user.status == "approved":
            return redirect("/staff/staff_dashboard")
        
        if this_user.role== "staff" and this_user.status == "pending":
            flash("wait for admin to approve you")
            return redirect("/login_page")
        
        #user
        if this_user.role == "user" :
            return redirect("/user/user_dashboard")
            
    return render_template("login_page.html")





# ===================================================logout=================================================================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")