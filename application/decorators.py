from functools import wraps
from flask import session , redirect, flash
from .models import User

# -------------login check ----------------
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Login first")
            return redirect("/login_page")
        
        user = User.query.filter_by(id= session.get("user_id")).first()
        if user is None:
            session.clear()
            flash("please login again")
            return redirect("/login_page")
        
        return func(*args, **kwargs)
    return wrapper

# --------admin role check---------------------------------
def admin_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get("role") != "admin":
            flash("Unauthorized access")
            return redirect("login_page")
        return func(*args, **kwargs)
    return wrapper

# --------staff role check ---------------------------------
def staff_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "staff":
            flash("Unauthorized access")
            return redirect("login_page")
        return func(*args,**kwargs)
    return wrapper

# ------------user role check-----------------
def user_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get("role") != "user":
            flash("Unauthorized access")
            return redirect("login_page")
        return func(*args, **kwargs)
    return wrapper
