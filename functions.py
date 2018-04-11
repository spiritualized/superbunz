import re, datetime
import bs4
from dateutil import parser

def write_str(str1, filename):
	f = open(filename, 'w')
	f.write(str1)
	f.close()

def get_fb_name(str1):
	soup = bs4.BeautifulSoup(str1, "html5lib")
	logout_str = soup.find("a", href=re.compile(r"\/logout\.php\?")).text

	match = re.search(r"(Log Out)|(Logout) \((.+?)\)", logout_str)
	if(match):
		return match.group(3)

def parse_age(str1):
	if "Just now" in str1:
		age = datetime.datetime.now()
	elif "min" in str1:
		age = datetime.datetime.now() - datetime.timedelta(minutes=int(str1.split(" ")[0]))
	elif "hr" in str1:
		age = datetime.datetime.now() - datetime.timedelta(hours=int(str1.split(" ")[0]))
	elif "Yesterday" in str1:
		age = parser.parse(str1.split(" at" )[1]) - datetime.timedelta(days=1)
	elif " at " in str1:
		str1 = str1.replace(" at ", " ")
		age = parser.parse(str1)
	else:
		raise ValueError("Unable to parse post age \"{0}\"".format(str1))

	return age

def format_name(str1):
	names = str1.split(" ")
	names[-1] = names[-1][0]+"."
	return " ".join([names[0], names[-1]])

def filter_plausible_costs(arr):
	if arr is None:
		return 0

	arr2 = []
	for i in arr:
		i2 = i.replace(",","")

		# skip values with > 4 digits
		if len(i2) > 4:
			continue
		i2 = int(i2)

		# filter out too-small values
		if i2 < 150:
			continue

		# filter out year-numbers
		if i2 > 2015 and i2 < 2020:
			continue

		arr2.append(i2)

	for i in arr2:
		# almost all real rents divide evenly into 5
		if i % 5 != 0:
			arr2.remove(i)
			arr2.append(i)

	if len(arr2) == 0:
		return 0

	return arr2[0]