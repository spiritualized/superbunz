
import os, sys, re, pickle, time
import requests
import urllib
import bs4
import json

from functions import *
from dbstuff import *
from config import *




group_base_url = "https://mbasic.facebook.com/groups/"
group_number = "985601841489998"

group_url = "{0}{1}".format(group_base_url, group_number)

facebook = requests.session()
facebook.headers.update({'User-Agent': user_agent})

db = database_init()

def login():
	# load existing cookies from last login
	cookies = None
	cookiejar_path = '{1}{0}session.dat'.format(os.sep, sys.path[0])
	if os.path.isfile(cookiejar_path):
		with open(cookiejar_path, "rb") as f:
		    facebook.cookies = pickle.load(f)

	# fetch a test page, checking if we are still logged in using the saved cookies
	test_page = facebook.get(group_url).text

	if "Your Pages" not in test_page:
		soup = bs4.BeautifulSoup(test_page, "html5lib")


		form_fields = soup.find("form", action=re.compile(r"\/login\.php\?")).findAll("input", type="hidden")
		

		# log in
		params = {}

		for i in form_fields:
			params[i["name"]] = i["value"]

		params["email"] = fb_email
		params["pass"] = fb_password
		params["login"] = "Log In"

		url_params = urllib.parse.urlencode({"refsrc":"https://mbasic.facebook.com/login/", "lvw":"101", "ref":"dbl"})

		r = facebook.post("https://mbasic.facebook.com/login.php?{0}".format(url_params), params)

		if "The password you entered is incorrect." in r.text:
			print("Login failed.")
			exit()

		# skip warning screen
		if "log in with one tap" in r.text.lower():
			r = facebook.get("https://mbasic.facebook.com/login/save-device/cancel/?flow=interstitial_nux&amp;nux_source=regular_login&amp;ref=dbl")

		print("Logged in as {0}".format(get_fb_name(r.text)))

	else:
		r = facebook.get("https://mbasic.facebook.com/")
		
		print("Resumed session as {0}".format(get_fb_name(r.text)))

	# write out our site/cloudflare cookies
	pickle.dump(facebook.cookies, open(cookiejar_path, "wb"))



def get_pages(limit):

	bacr = ""

	for page_num in range(0, limit):

		r = facebook.get(group_url+"?bacr="+bacr)
		soup = bs4.BeautifulSoup(r.text, "html5lib")

		bacr = soup.find("a", href=re.compile(r"/groups/\d+\?bacr=(.*)"))["href"].split("bacr=")[1]

		page_stories = soup.find(id="m_group_stories_container").findAll(role="article")

		stories = []

		for story in page_stories:

			# possible bug
			if not story.has_attr("data-ft"):
				continue

			data = json.loads(story["data-ft"])

			# skip promotional posts
			if "top_level_post_id" not in data:
				continue


			poster = story.find("table", role="presentation").findAll("td")[1].findAll("strong")[0]
			name = poster.text
			username = re.search(r"^/([\w\.]*)\?", poster.find("a")["href"]).group(1)
			posted = parse_age(story.find("abbr").text)

			if username == "profile.php":
				username = re.search(r"^/profile\.php\?id=([\w\.]*)&", poster.find("a")["href"]).group(1)

			story_id = data["mf_story_key"]

			reactions = story.find(id="like_{0}".format(story_id)).find("a").text
			if reactions == "Like":
				reactions = 0
			reactions = int(reactions)

			picture = story.find("a", href=re.compile(r"^/photo\.php\?fbid="))
			if picture:
				picture = picture.find("img")
			else:
				picture = ""

			if picture:
				picture = picture["src"]
			else:
				picture = ""

			stories.append({'name':name, 'posted': posted, 'username':username, 'story_id':story_id, 'reactions':reactions, 'picture':picture, 'description':""})

		for story in stories:
			new_story = Story(story['story_id'], story['posted'], story['name'], story['username'], story['reactions'], story['picture'])

			db.merge(new_story)
			db.commit()

		# fill user_id
		new_users = db.query(Story).filter_by(description=None).all()
		for new_user in new_users:
			r = facebook.get("https://mbasic.facebook.com/{0}".format(new_user.username))
			soup = bs4.BeautifulSoup(r.text, "html5lib")
			user_id = soup.find("a", href=re.compile(r"/mbasic/more/\?owner_id=(\d+)"))['href']
			new_user.user_id = re.search(r"owner_id=(\d+)", user_id).group(1)

			r = facebook.get("https://graph.facebook.com/{0}/picture?type=normal".format(new_user.user_id))
			new_user.user_picture = r.url

			db.commit()

		# fill description
		new_posts = db.query(Story).filter_by(description=None).all()
		for new_post in new_posts:
			r = facebook.get("{0}?view=permalink&id={1}".format(group_url, new_post.story_id))
			soup = bs4.BeautifulSoup(r.text, "html5lib")

			if soup.find("title").text == "Content Not Found":
				db.delete(new_post)
				continue

			# find the subdiv containing one or more <p>, a semi-robust way of finding the story text
			possible_paragraphs = soup.find(id="m_story_permalink_view").find("div").find("div").find("div").findAll("div")#[3]
			description = ""
			for pp in possible_paragraphs:
				if pp.find("p"):
					paragraphs = pp.findAll("p")
					#print(paragraphs)
					for p in pp:
						description += p.text+ "\n"
					description = description.strip()
					break
			new_post.description = description

			# extract the listing cost			
			result = re.search(r"\$([,]?\d[,]?\d[,]?\d+)", new_post.description) # search for $1200, $1,200 style values
			new_post.cost = 0
			if result:
				new_post.cost = int(result.group(1).replace(",",""))

			# look for 3-4 digit numbers which aren't a year
			else:
				result = re.findall(r"([,]?\d[,]?\d[,]?\d+)", new_post.description)
				if result:
					new_post.cost = filter_plausible_costs(result)

			# check if marked sold
			if "(Sold)" in new_post.description:
				new_post.sold = True
			else:
				new_post.sold = False

			if new_post.picture == "" or new_post.cost == 0:
				new_post.category = "Other"
			else:
				new_post.category = "Offered"

			db.commit()

		new_posts = db.query(Story).all()
		for new_post in new_posts:

			db.commit()

		print("Scanned page {0}".format(page_num))


#description = ""
#for paragraph in post.find("div").findAll("div")[3].find("span").findAll("p"):
#	description += "\n" + paragraph.text
#print(description)

#print("{2} - {0} - {1}".format(name, username, story_id))



login()

get_pages(20)
last_full_scrape = datetime.datetime.now()
while True:

	get_pages(1)

	# if it's been more than 30 minutes since the last full scrape
	if last_full_scrape < datetime.datetime.now() - datetime.timedelta(minutes=30):
		get_pages(20)
		last_full_scrape = datetime.datetime.now()

	time.sleep(300)