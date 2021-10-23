'''
Initially followed this YouTube tutorial, for user authentication: l:https://github.com/PrettyPrinted/building_user_login_system

Things I'm still not sure how to do:
1. Minimize FOUC so it doesn't flash white on each new page (if that's still happening)
2. Change the color of a link as your mouse hovers over it (Though now, don't want that anyway.)
3. Use jinja to change the CSS :root variables (CSS mods currently work, but currently aren't as neat as they could be.)
'''
import numpy as np
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, DateField, SelectField, SubmitField#Boolean field is checkbox
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import InputRequired, Email, Length, DataRequired, EqualTo, ValidationError
import email_validator
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
import random
import calendar #ticks
import datetime
from datetime import timedelta
from operator import attrgetter
from webcolors import rgb_to_hex #autostyle
from colorthief import ColorThief
#from magic_background import magic_background
#from wiki2artifacts import wiki2artifacts #autopopulate db
from anystring2date import anystring2date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer #email reset
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt

import operator
from sqlalchemy.sql import select, text

app = Flask(__name__)
app.config.from_object(__name__) # Because of:  https://stackoverflow.com/questions/17404854/connection-refused-when-sending-mail-with-flask-mail
Bootstrap(app)
file_path = os.path.join(os.path.abspath(os.getcwd()),"database.db")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'+file_path
app.config['SECRET_KEY'] = 'meow'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thymelimne@gmail.com'#os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = 'timelinepassword'#os.environ.get('EMAIL_PASS')
mail = Mail(app)

bcrypt = Bcrypt(app)

#===============================================================
# User authentication

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(), unique=True)
	email = db.Column(db.String(50), unique=True)
	password = db.Column(db.String(80))
	#------------------------------------------
	def get_reset_token(self, expires_sec=1800):
		s = Serializer(app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'user_id': self.id}).decode('utf-8')

	@staticmethod
	def verify_reset_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			user_id = s.loads(token)['user_id']
		except:
			return None
		return User.query.get(user_id)

	def __repr__(self):
		return f"User('{self.username}', '{self.email}')"
	#-------------------------------------------

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class LoginForm(FlaskForm):
	#Three fields.
	username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
	password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
	
class RegisterForm(FlaskForm):
	#username, email, and password fields.
	email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
	username = StringField('username', validators = [InputRequired(), Length(min=4, max=15)])
	password = PasswordField('password', validators = [InputRequired(), Length(min=8, max=80)])

#@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	# Login form is a little more complicated than signup form, but it's still pretty easy.
	form = LoginForm()
	if form.validate_on_submit():
		print("here")
		user = User.query.filter_by(username=form.username.data).first()
		if user:
			print("there is a user")
			correct_password_hash = user.password
			hashed_inputted_password = generate_password_hash(form.password.data, method='sha256')
			print(correct_password_hash)
			print(form.password.data)
			if check_password_hash(user.password, form.password.data):
				print("correct password")
				login_user(user)#, remember=form.remember.data)
				#return redirect(url_for('dashboard'))
				return redirect(url_for('create'))
			else:
				print("Password is incorrect")
		return render_template('login_error.html')
	return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = RegisterForm()
	if form.validate_on_submit():
		hashed_password = generate_password_hash(form.password.data, method='sha256')
		new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		try:
			db.session.add(new_user)
			db.session.commit() #Add vs. commit -- idk lol, but u gotta do it
		except:
			return render_template('signup_error.html')
		return render_template('created.html', typeofthing="account")
	return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
	return render_template('dashboard.html', name=current_user.username)
	
@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('create'))


@app.route('/create')
def create():
	try:
		name=current_user.username
	except:
		name=""
	return render_template("create.html", name=name)
	
#-------------------------------------------------------------------
# admin-specific priveledges:

# Users:
@app.route('/allusers')
@app.route('/all_users')
@app.route('/allusersadmin')
@app.route('/all_users_admin')
@login_required
def all_users():
	if current_user.username=="admin":
		users = User.query.all()
		return render_template('all_users.html', users=users)
	else:
		return redirect(url_for('create'))

@app.route('/deleteuser/<userid>')
@app.route('/delete_user/<userid>')
@login_required
def delete_user(userid):
	if current_user.username=="admin":
		u = User.query.filter(User.id==userid).first()
		db.session.delete(u)
		db.session.commit()
		return redirect(url_for('all_users'))
	else:
		return redirect(url_for('create'))
	
	
	
	
# Topics:
@app.route('/alltopicsadmin')
@app.route('/all_topics_admin')
@login_required
def all_topics_admin():
	if current_user.username=="admin":
		topics = Topic.query.all()
		return render_template('all_topics_admin.html', topics=topics)
	else:
		return redirect(url_for('create'))

@app.route('/deletetopic/<topicid>')
@app.route('/delete_topic/<topicid>')
@login_required
def delete_topic(topicid):
	if current_user.username=="admin":
		t = Topic.query.filter(Topic.tid==topicid).first()
		db.session.delete(t)
		db.session.commit()
		return redirect(url_for('all_topics_admin'))
	else:
		return redirect(url_for('create'))
		
		
		
		
		
		
# Artifacts:
@app.route('/allartifactsadmin')
@app.route('/all_artifacts_admin')
@login_required
def all_artifacts_admin():
	if current_user.username=="admin":
		artifacts = Artifact.query.all()
		return render_template('all_artifacts_admin.html', artifacts=artifacts)
	else:
		return redirect(url_for('create'))

@app.route('/deleteartifact/<artifactid>')
@app.route('/delete_artifact/<artifactid>')
@login_required
def delete_artifact(artifactid):
	if current_user.username=="admin":
		a = Artifact.query.filter(Artifact.aid==artifactid).first()
		db.session.delete(a)
		db.session.commit()
		return redirect(url_for('all_artifacts_admin'))
	else:
		return redirect(url_for('create'))
		
		
		
		
	
#==============================================================
# The classes defining the actual interesting meat of the project:

class Topic(db.Model):
	tid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String(), unique=True)
	#artifacts = db.relationship('Artifact', backref='topic', lazy=True)
	style = db.relationship('Style', backref='atopic', lazy=True)
	artifacts = db.relationship('Artifact', backref='topic', lazy=True)
db.create_all()
class Artifact(db.Model):
	aid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String())
	description = db.Column(db.String())
	date = db.Column(db.Date(), nullable=False)
	url = db.Column(db.String())
	atopic = db.Column(db.Integer, db.ForeignKey('topic.tid'), nullable=False)
db.create_all()
# auto-styling is a thing this website does.
class Style(db.Model):
	sid = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String())
	topic = db.Column(db.Integer, db.ForeignKey('topic.tid'), nullable=False)
	imgurl = db.Column(db.String())
	#-----------------------------------
	colors = db.Column(db.String()) #np string representation of a list
	tibidi = db.Column(db.String()) #np string representation of a list
		#^ [tackiest_index, brightest_index, darkest_index]
db.create_all()
	
#==================================================
# Autostyle:
	
# Notice how there's no style form? :) All it needs to go off of is the title of the topic, and it uses that string to make the aesthetic.
def color_knowledge(img, imgurl):
	print(imgurl)
	colorthief = ColorThief(imgurl)
	palette = colorthief.get_palette(quality=1000, color_count=10)
	
	brightness = []
	tackiness = []
	for p in palette:
		brightness.append(sum(p))
		tackiness.append(np.var(p))
		
	return colorthief, palette, brightness, tackiness

# Returns a tibidi (not packaged as a single list)
def colorbychance(ct, p, b, t):
	ti, bi, di = random.sample(range(len(p)),3)
	b_inorder = b.sort()
	t_inorder = t.sort()
	ti_picked = random.choice(t[-3:])
	bi_picked = random.choice(b[-3:])
	di_picked = random.choice(b[:2])
	print(p)
	print(p)
	print(p)
	print(type(p))
	for i in range(len(p)):
		if t[i]==ti_picked:
			ti = i
		if b[i]==bi_picked:
			bi = i
		if b[i]==di_picked:
			di = i
	if ti==bi or ti==di or bi==di:
		return colorbychance(ct, p, b, t)
	return ti, bi, di
	
def autostyle(topic_name, topic_index):
	# Proud of the magic_background module, but will have to circumbent it for now:
	'''img, imgurl = magic_background.magic_background(topic_name)'''
	
	img=None; imgurl="static/starrysky.jpg"
	ct, p, b, t = color_knowledge(img, imgurl)
	print(p)
	
	#Will want the colors from the palette representable in HTML-friendly hex form, so do that here:
	colors = []
	for rgbcolor in p:
		colors.append(rgb_to_hex(rgbcolor))
	
	'''
	#ti means tackiest_index
	ti = min(range(len(t)), key=t.__getitem__)
	
	#Doing a little cheat to get the brightness extremes; temporarily taking out the ti (so bi =/= ti) but then afterward the tackiest color will go back into the brightness measure... Or not, depending on list b will even get used after this function.
	bti = b[ti]
	b[ti] = (min(b) + max(b)) / 2 #lazy, not watertight way to hopefully ensure that b[ti] won't be considered the brightest OR the darkest...
	
	#bi means brightest_index
	bi = b.index(max(b))
	
	#di means darkest_index
	di = b.index(min(b))
	'''
	#--------------------------------------------
	# Redoing it all -- hopefully get better colors here:
	ti, bi, di = colorbychance(ct, p, b, t)
	
	#Now, put it in the table :)
	new_style = Style(title=topic_name, topic=topic_index, imgurl=imgurl, colors=np.array2string(np.array(colors)), tibidi=np.array2string(np.array([ti,bi,di])))
	db.session.add(new_style)
	db.session.commit()
	
#Got so sick of debugging external array-to-list methods, we'll just do it the slow way:
def string2array(string):
	string = re.sub("[\[\]\n\']","",string)
	array = string.split(" ")
	return array
	
@app.route('/swatch')
def swatch():
	topic = request.args.get('topic')
	if topic==None:
		topic = 1
	style = Style.query.filter(Style.topic==topic).first()
	colors = string2array(style.colors)
	tibidi = string2array(style.tibidi)
	topic = Topic.query.filter(Topic.tid==topic).first()
	return render_template('swatch.html', style=style, colors=colors, topic=topic, tibidi=tibidi)
	
#===================================================
# Forms:

class CreateTopicForm(FlaskForm):
	title = StringField('title', validators=[InputRequired(), Length(min=1, max=30)])
	panels = BooleanField('make background panels')
	collaborative = BooleanField('enable other users to contribute')
class CreateArtifactForm(FlaskForm):
	title = StringField('title', validators=[InputRequired(), Length(min=1, max=100)])
	description = StringField('description')
	date = DateField('date (MM/DD/YYYY)', format='%m/%d/%Y')
	url = StringField('url')
	atopic = SelectField('atopic', choices=db.session.query(Topic.title).all())
	
	#The following is what helps make sure that the topics list is updated, for the SelectField in this form.
	def __init__(self, *args, **kwargs):
		super(CreateArtifactForm, self).__init__(*args, **kwargs)
		self.atopic.choices = [(a.tid, a.title) for a in Topic.query.order_by(Topic.title)]
	
@app.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
	form = CreateTopicForm()
	if form.validate_on_submit():
		
		#Check to make sure that it doesn't already exist:
		if not Topic.query.filter(Topic.title==form.title.data).count():
			new_topic = Topic(title=form.title.data)
			db.session.add(new_topic)
			db.session.commit()
		
			# Create the style:
			autostyle(new_topic.title, new_topic.tid)
		
		return render_template('created.html', typeofthing="topic")
	return render_template('create_topic.html', form=form)
	
#HTML USED: create_artifact.html
@app.route('/create_artifact', methods=['GET', 'POST'])
@login_required
def create_artifacts():
	form = CreateArtifactForm()
	if form.validate_on_submit():
		
		title = form.title.data
		description = form.description.data
		date = form.date.data
		url = form.url.data
		atopic = form.atopic.data
		
		print(title)
		print(description)
		print(date)
		print(url)
		print(int(atopic))
		
		new_artifact = Artifact(title=form.title.data, description=form.description.data, date=form.date.data, url=form.url.data, atopic=form.atopic.data) #atopic=Topic(tid=int(form.atopic.data)))
		db.session.add(new_artifact)
		db.session.commit()
		return render_template('created.html', typeofthing="artifact")
	return render_template('create_artifact.html', form=form)

#=============================================================
# ???:

# Starting off real simple: just display the artifacts.
@app.route('/all_artifacts')
def all_artifacts():
	artifacts=Artifact.query.all()
	return render_template('all_artifacts.html', artifacts=artifacts)
	
# Helper function to decide where to locate the things.
def find_extreme_dates(items):
	earliest_date = None
	latest_date = None
	if items:
		earliest_date = items[0].date
		latest_date = items[0].date
	for item in items:
		if item.date < earliest_date:
			earliest_date = item.date
		if item.date > latest_date:
			latest_date = item.date
	return earliest_date, latest_date
	
def find_relative_lengths(items, overall_depth, start_depth):
	start_date, end_date = find_extreme_dates(items)
	overall_length = end_date - start_date
	
	# This'll probably happen if there are no artifacts listed for the topic, because...
	# The query to get artifacts of a specified topic would return an empty set.
	# & of course, the maximum distance of scalars within an empty set, would... probably be zero? Or infinity. Either way, Python seems to assume it as zero in this setting.
	if overall_length==0:
		print("For anyone who is reading the console, you might be interested to learn that the find_relative_lengths() method is returning None, perhaps because the function was given an empty set...")
		return None
	
	lengths = {}
	depths = {}
	
	# To help measure the distance between things:
	previous_absolute_depth = -100
	
	# To tell you when the years is:
	years = {}
	
	for item in items:
		time_since_start = item.date - start_date
		relative_length = time_since_start / overall_length
		relative_length_dict = {item.aid : relative_length}
		absolute_depth=relative_length*overall_depth+start_depth
		absolute_depth_dict = {item.aid : absolute_depth}
		lengths.update(relative_length_dict)
		depths.update(absolute_depth_dict)
		
		if not item.aid in years:
			if not item.date.year in years.values():
				years[item.aid] = item.date.year
			else:
				years[item.aid] = " "
		
		# To fix the scaling issue (More patchy than it is optimal, as a solution, but hopefully works):
		depth_difference = absolute_depth - previous_absolute_depth
		if depth_difference < 2.5 and not depth_difference<=0:
			print(depth_difference)
			return find_relative_lengths(items, 2*overall_depth, start_depth)
		previous_absolute_depth = absolute_depth
	print(years)
	return lengths, depths, overall_depth, years
	
#Find the absolute pixel depths for each item. 
def find_absolute_depths(artifacts, start_depth, overall_depth, relative_depths):
	absolute_depths = []
	for artifact in artifacts:
		absolute_depth = start_depth + overall_depth * relative_depths[artifact.aid]
		localdict = {artifact.aid : absolute_depth}
		absolute_depths.append(localdict)
	return absolute_depths
	

	
#=====================================================
# The front-facing pages:
	
@app.route('/timeline')
def timeline():
	topic_name = request.args.get('topic')
	if topic_name==None:
		topic_name = random.randrange(1, Topic.query.count())
		
	colors=None
	tackycolor='brown'
	brightcolor='eggshell'
	darkcolor='black'
	imgurl=None
	style = Style.query.join(Topic).filter(Topic.title==topic_name).first() #hope this works?
	if style:

		colors = style.colors
		colors = re.sub("[\[\]\n\']","",colors)
		#Got so sick of debugging external array-to-list methods, we'll just do it the slow way:
		colors = colors.split(" ")
		tibidi = style.tibidi
		ti = int(tibidi[1])
		bi = int(tibidi[3])
		di = int(tibidi[5])
		tackycolor = colors[ti]
		brightcolor = colors[bi]
		darkcolor = colors[di]
		
		imgurl=style.imgurl
		
	print(topic_name)	
	ticks = request.args.get('ticks')
	overall_depth=1000
	start_depth = 0
	
	artifacts = Artifact.query.join(Topic).filter(Topic.tid==topic_name).order_by(Artifact.date)
	topic = Topic.query.filter(Topic.tid==topic_name).first()
	if not str(topic_name).isnumeric():
		artifacts = Artifact.query.join(Topic).filter(Topic.title==topic_name).all()
		topic = Topic.query.filter(Topic.title==topic_name).first()
			
	if not artifacts:
		return render_template('empty_topic.html', topic=topic)
		
	if len(artifacts)==1:
		artifact = artifacts[0]
		return render_template('one_topic.html', topic=topic, artifact=artifact)
	
	# And the following is what is intended to happen from this function:
	relative_depths, absolute_depths, overall_depth, years = find_relative_lengths(artifacts, overall_depth, start_depth)
	
	month_ticks = None
	week_ticks = None
	if ticks:
		month_ticks = create_ticks(artifacts, overall_depth=overall_depth, start_depth=start_depth)
		print(month_ticks)
		for tick in month_ticks:
			print(tick[2])
	
	return render_template('timeline.html', artifacts=artifacts, relative_depths=relative_depths, overall_depth=overall_depth, start_depth=start_depth, absolute_depths=absolute_depths, topic=topic, ticks=ticks, month_ticks=month_ticks, num_artifacts=len(artifacts), tackycolor=tackycolor, panelcolor=brightcolor, textcolor=darkcolor, imgurl=imgurl, style=style, years=years)
	
	
def getvideocode(youtubeurl):
	videocode = youtubeurl
	videocode = videocode.partition('?v=')[2]
	videocode = videocode.partition('?')[0]
	print("getvideocode()")
	print(videocode)
	return videocode
	
@app.route('/artifact')
def artifact():

	# given in the URL: localhost.com/artifact?artifact=<artifact id or title>
	input = request.args.get('artifact')
	
	# If no artifact given, let's just do a random artifact whynot.
	if not input:
	
		input = random.randrange(1,Artifact.query.count()) # Remember that you can't query to the 0th Artifact... it seems like the autoincrement starts from 1.
		
	# Now, give the URL the chance to give either an int input (to be the id of an artifact) or a string input (to be the title of an artifact)
	if str(input).isnumeric():
		artifact = Artifact.query.get(input)
	else:
		artifact = Artifact.query.filter(Artifact.title==input)
		
	# Artifact might be None, so I'll try to make sure it's not that.
	if artifact:
		topic = Topic.query.get(artifact.atopic)
		if "youtube" in artifact.url:
			return render_template('artifact.html', artifact=artifact, topic=topic, videocode=getvideocode(artifact.url))
		return render_template('artifact.html', artifact=artifact, topic=topic)
		
	# If artifact was None:
	return '<h1>Oops... looks like there was probably no artifact to present.</h1>'
	

@app.route('/')
@app.route('/home')
@app.route('/topics')
@app.route('/timelines')
def timelines():
	topics = Topic.query.all()
	return render_template('topics.html', topics=topics)
	
#===============================================================
# I was too lazy to manually create example artifacts, so I made a module to scrape tables on Wikipedia, to make each timeline more quickly.
def isdayofweek(word):
	weekdays = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
	if word in weekdays:
		return True
	else:
		return False
def ismonth(word):
	months = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
	if word.lower()[:2] in months:
		return True
	else:
		return False
# :| couldn't find a function that converts "May 2, 2008" to "05/02/2008" so i make it
def month_string_to_number(string):
	'''
	Copypasted this function from:	https://stackoverflow.com/questions/3418050/month-name-to-month-number-and-vice-versa-in-python
	'''
	m = {
		'jan': 1,
		'feb': 2,
		'mar': 3,
		'apr':4,
		 'may':5,
		 'jun':6,
		 'jul':7,
		 'aug':8,
		 'sep':9,
		 'oct':10,
		 'nov':11,
		 'dec':12
		}
	s = string.strip()[:3].lower()
	print(s)

	try:
		out = m[s]
		return out
	except:
		raise ValueError('Not a month')
def convertdatetime(string): #string
	if string:
		a = string
		print("a")
		print(a)
		b = re.sub(",","",a)
		print('b')
		print(b)
		c = str.split(b)
		print('c')
		print(c)
		things = c
		print('things')
		print(things)
		#c[0] = month_string_to_number(c[0])
		#[0] month [1] day [2] year
		#d = str(c[0])+"/"+str(c[1])+"/"+str(c[2])
		monthindex = -1
		dayindex = -1
		yearindex = 0
		for i in range(2):
			if not things[i].isnumeric():
				if ismonth(things[i]):
					monthindex = i
					things[i] = month_string_to_number(things[i])
			elif len(things[i])==4:
				yearindex = i
			else:
				dayindex = i
		year=int(things[yearindex])
		if monthindex==-1:
			month=1
		else:
			month=int(things[monthindex])
		if dayindex==-1:
			day=1
		else:
			day=int(things[dayindex])
		return datetime.date(year,month,day)
	return None


		
def addtopic(title):
	new_topic = Topic(title=title)
	tid = new_topic.tid
	db.session.add(new_topic)
	db.session.commit()
	tid = Topic.query.filter(Topic.title==title).first().tid
	return tid
	
	

			
@app.route('/about')
def about():
	return render_template('about.html')



@app.route('/remove_duplicate_artifacts')
def remove_duplicate_artifacts():
	new_artifacts=[]
	artifacts = Artifact.query.all()
	artifacts.sort(key=lambda a: a.date)
	previous_artifact = Artifact(title=None, date=None)
	print(previous_artifact)
	for artifact in artifacts:
		current_artifact=artifact
		repeat_title = (current_artifact.title==previous_artifact.title)
		repeat_date = (current_artifact.date==previous_artifact.date)
		if (not repeat_date) or (not repeat_title):
			new_artifacts.append(current_artifact)
			print(str(current_artifact.title)+"\t"+str(current_artifact.date)+"\t"+str(current_artifact.aid))
		previous_artifact = current_artifact
	
	for a in Artifact.query.all():
		if a not in new_artifacts:
			db.session.delete(a)
			db.session.commit()
	
	return redirect(url_for('timelines'))
	
	
	
class EditArtifactForm(FlaskForm):
	artifactDescription = StringField('description')
	artifactUrl = StringField('url')

# https://stackoverflow.com/questions/35892144/pre-populate-an-edit-form-with-wtforms-and-flask
@app.route('/editartifact/<artifactId>', methods = ['GET','POST'])
def editartifact_page(artifactId):
	print("editartifact_page()")
	try:
		form = EditArtifactForm()		
		if request.method=="POST" and form.validate():
			artifactDescription = form.artifactDescription.data
			artifactUrl = form.artifactUrl.data
			print(artifactDescription)
			print(artifactUrl)
			
			artifact = Artifact.query.filter(Artifact.aid==artifactId).first()
			print(artifact)
			
			artifact.description = artifactDescription
			artifact.url = artifactUrl
			db.session.commit()
			return redirect(url_for('timelines'))
		return render_template("editartifact2.html", form=form, ARTIFACT_ID=artifactId)

	except Exception as e:
		return(str(e))

db.create_all()
from resetemail import *
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
	
