from flask import Flask
app = None
from application.database import db

def create_application():
    app = Flask(__name__) # this line tells flask that treat file app.py as server code 
    app.secret_key = "secret_key"
    app.debug = True # apply changes without reruning application, tell error in more detail 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ep-rose.sqlite3'
    db.init_app(app)
    app.app_context().push() 
    return app

app = create_application()

# why import * (import everything)?-> because controller file comtains all routes 
from application.controllers import *
# becasue if i do 
#                from controllers import *
# thsi will start searching my controllers file into root folder but it lies in applciation folder

if __name__ == "__main__" :
    with app.app_context(): # when ever my app context is created or app runs
        db.create_all()  # database is created 
        # like when i start my app first then create my database if i rerun my app then the database will not created again
       
        Admin = User.query.filter_by(user_name='robin', role='admin').first()
        if Admin is None :
            Admin = User(user_name='robin', role='admin', email='admin_robin@gmail.com', password='robin')
            db.session.add(Admin)
            db.session.commit()

    app.run()
