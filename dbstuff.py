import datetime
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.dialects.mysql

from config import *

Base = sqlalchemy.ext.declarative.declarative_base()

# connect to database
def database_init():

	engine = None
	if use_mysql is True:
		engine = sqlalchemy.create_engine("mysql+pymysql://{0}:{1}@{2}/{3}?charset=utf8mb4".format(mysql_username, mysql_password, mysql_host, mysql_db), encoding='utf-8', pool_size=10)
	else:
		engine = sqlalchemy.create_engine("sqlite:///sqlite.db")

	Base.metadata.create_all(engine)

	db = sqlalchemy.orm.sessionmaker(engine)

	return sqlalchemy.orm.scoped_session(db)

class Story(Base):
	__tablename__ = "posts"

	story_id = sqlalchemy.Column(sqlalchemy.String(16), primary_key=True)
	posted = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
	name =  sqlalchemy.Column(sqlalchemy.String(512), nullable=False)
	username =  sqlalchemy.Column(sqlalchemy.String(512), nullable=False)
	user_id = sqlalchemy.Column(sqlalchemy.String(16))
	cost = sqlalchemy.Column(sqlalchemy.Integer)
	reactions = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
	user_picture = sqlalchemy.Column(sqlalchemy.Text)
	picture = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
	description = sqlalchemy.Column(sqlalchemy.Text)

	category = sqlalchemy.Column(sqlalchemy.Enum('Offered', 'Other'))
	sold = sqlalchemy.Column(sqlalchemy.Boolean)

	def __init__(self, story_id, posted, name, username, reactions, picture):
		self.story_id = story_id
		self.posted = posted
		self.name = name
		self.username = username
		self.reactions = reactions
		self.picture = picture


class User(Base):
	__tablename__ = "users"

	token =  sqlalchemy.Column(sqlalchemy.String(36), primary_key=True)
	views = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
	ip_addr = sqlalchemy.Column(sqlalchemy.String(160), primary_key=True)
	access_first = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
	access_last = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
	hide_sold = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)
	max_cost = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

	def __init__(self, token, ip_addr):
		self.token = token
		self.views = 1
		self.ip_addr = ip_addr
		self.access_first = datetime.datetime.now()
		self.access_last = datetime.datetime.now()
		self.hide_sold = True
		self.max_cost = 2000

class UserStory(Base):
	__tablename__ = "user_stories"

	story_id = sqlalchemy.Column(sqlalchemy.ForeignKey(Story.story_id, ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
	token =  sqlalchemy.Column(sqlalchemy.ForeignKey(User.token, ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

	def __init__(self, story_id, token):
		self.story_id = story_id
		self.token = token