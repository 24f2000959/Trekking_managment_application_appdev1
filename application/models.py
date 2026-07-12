from .database import db

# from database import db --> app out of context
# from application.database import db --> error because model and doesnot have any application folder 

from datetime import date


# ======================================================== User ===================================================
class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(),nullable=False, default='user')    # role -> admin, staff, user
    status = db.Column(db.String(20), default="pending") # pending, approve, blacklist
    date = db.Column(db.Date, default=date.today)


    # Relationships
    treks = db.relationship("Trek", backref="staff", lazy=True)
    bookings = db.relationship("Booking", backref="user", lazy=True)



# ======================================================== terk ===================================================
class Trek(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    trek_name = db.Column(db.String(), nullable=False)
    location = db.Column(db.String(), nullable=False)
    difficulty = db.Column(db.String(), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)

    start_date = db.Column(db.Date(), nullable=False)
    end_date = db.Column(db.Date(), nullable=False)

    description = db.Column(db.Text())
    status = db.Column(db.String(), default="Open")

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Relationships
    bookings = db.relationship("Booking", backref="trek", lazy=True)



# ======================================================== Booking ===================================================
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
                        db.Integer, 
                        db.ForeignKey("user.id"), 
                        nullable=False)

    trek_id = db.Column(
                        db.Integer, 
                        db.ForeignKey("trek.id"), 
                        nullable=False)

    booking_date = db.Column(db.Date, default=date.today)

    booking_status = db.Column(db.String(20), default="Booked")

