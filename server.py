import json, uuid, datetime, math, random, string

from flask import Flask, render_template, request, make_response, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
from functools import wraps

from functions import *
from config import *
from dbstuff import *

# flask app
app = Flask(__name__, static_folder='static')
app.debug = True
app.secret_key = secret_key
version = '1.0.3'

# db stuff
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://{0}:{1}@{2}/{3}?charset=utf8mb4".format(mysql_username, mysql_password, mysql_host, mysql_db)
db = SQLAlchemy(app)

blueprint = Blueprint('bunz', __name__, static_folder='static', url_prefix=url_prefix)

@blueprint.route('/')
def index():

	token = request.cookies.get("token")
	user = db.session.query(User).filter_by(token=token).first()
	response = make_response(render_template("template.html", version=version, google_analytics_id=google_analytics_id, url_prefix=url_prefix))

	if not token or not user:
		token = str(uuid.uuid4())
		db.session.add(User(token, request.environ['REMOTE_ADDR']))
		db.session.commit()
		response.set_cookie('token', token)
	else:
		user.views += 1
		user.access_last = datetime.datetime.now()
		db.session.commit()

	return response

def format_results(results, user):
	stories = []

	saved = []
	user_stories = db.session.query(UserStory).filter_by(token=user.token).all()
	for s in user_stories:
		saved.append(s.story_id)

	for r in results:
		fields = {}
		for field in [x for x in dir(r) if not x.startswith('_') and x != 'metadata']:
			data = r.__getattribute__(field)
			try:
				json.dumps(data) # this will fail on non-encodable values, like other classes
				fields[field] = data
			except TypeError:
				fields[field] = None

		age = datetime.datetime.now() - r.posted
		if age < datetime.timedelta(minutes=1):
			fields['age'] = "{0} secs ago".format(math.floor(age.total_seconds()))
		elif age < datetime.timedelta(hours=1):
			fields['age'] = "{0} mins ago".format(math.floor((age.total_seconds())/60))
		elif age < datetime.timedelta(days=1):
			fields['age'] = "{0} hrs ago".format(math.floor((age.total_seconds())/60/60))
		else:
			fields['age'] = "{0} days ago".format(math.floor((age.total_seconds())/60/60/24))

		fields['name'] = format_name(fields['name'])
		fields['description'] = fields['description'].replace("\n", "<div style=\"height:3px;\"></div>")

		if fields['cost'] == 0:
			fields['cost'] = ""
		else:
			fields['cost'] = "${0}".format(fields['cost'])

		fields['saved'] = 0
		if fields['story_id'] in saved:
			fields['saved'] = 1

		stories.append(fields)

	return stories

@blueprint.route('/api')
def api():

	user = db.session.query(User).filter_by(token=request.cookies.get("token")).first()
	if user:
		user.views += 1
		user.access_last = datetime.datetime.now()
		db.session.commit()
	else:
		return ""

	response = {}

	if request.args.get('op') == 'get_data':

		query = db.session.query(Story).filter_by(category="Offered").filter(Story.posted > datetime.datetime.now() - datetime.timedelta(days=8)).filter(Story.cost < user.max_cost).order_by(Story.posted.desc())
		if user.hide_sold:
			query = query.filter_by(sold=False)
		results = query.all()
		offers = format_results(results, user)

		query = db.session.query(Story).filter_by(category="Other").filter(Story.posted > datetime.datetime.now() - datetime.timedelta(days=8)).filter(Story.cost < user.max_cost).order_by(Story.posted.desc())
		if user.hide_sold:
			query = query.filter_by(sold=False)
		results = query.all()
		other = format_results(results, user)

		saved = []
		results = db.session.query(UserStory).filter_by(token=user.token)
		for result in results:
			saved.append(result.story_id)

		results = db.session.query(Story).filter(Story.story_id.in_(saved)).order_by(Story.posted.desc()).all()
		saved = format_results(results, user)

		query = db.session.query(Story).order_by(Story.posted.desc())

		users_online = db.session.query(User).filter(User.access_last > datetime.datetime.now() - datetime.timedelta(minutes=5)).count()

		max_cost = user.max_cost
		if max_cost == 99999:
			max_cost = ""

		response = {	'version': version, 
						'users_online': users_online, 
						'hide_sold': user.hide_sold,
						'max_cost': max_cost,
						'offers':offers,
						'other':other,
						'saved':saved,
					};


	elif request.args.get('op') == 'hide_sold':
		if request.args.get('hide_sold') == 'false':
			user.hide_sold = False
		else:
			user.hide_sold = True
		db.session.commit()

	elif request.args.get('op') == 'max_cost':
		try:
			user.max_cost = int(request.args.get('max_cost'))
		except:
			pass
		
		if request.args.get('max_cost') == "":
			user.max_cost = 99999

		db.session.commit()

	elif request.args.get('op') == 'save':
		if request.args.get('existing') == '1':
			user_story = db.session.query(UserStory).filter_by(story_id=request.args.get('story_id'), token=user.token).delete()
		else:
			db.session.add(UserStory(request.args.get('story_id'), user.token))

		db.session.commit()


	return json.dumps(response)


if __name__ == '__main__':

	app.register_blueprint(blueprint)
	app.run()


