from flask import Flask, render_template, redirect, request, url_for, flash, session
from datetime import datetime

from flask import current_app as app
# we cannot do somethign like this 
#                                 from .app import app
# because it creates circular importing error 
# we are importing app to controllers.py file and importing controller to app.py file .this cause circular import error
# so to concur this we do importing as form current_app as app

from .models import *


