# Author: Joseph McCullough (@joe_query, joseph@vertstudios.com)
# Functions for the toggl command line interface.

# Note for myself: Use "http://httpbin.org/post" when needed for testing.

import getpass, requests, simplejson, os, time, datetime
from urllib import urlencode

def api(key, params=None):
	'''
	Return the API url call. 
	Potential keys:
		me
		time_entries
		workspaces
		clients
		projects
		tasks
		tags
		users

	For more info, see https://www.toggl.com/public/api

	params is a dictionary of key value pairs
	'''

	if params:
		apiCall =  API_PREFIX + key + ".json?" + urlencode(params)
	else:
		apiCall =  API_PREFIX + key + ".json"
	return apiCall

def session(headers=None):
	'''
	Session wrapper for convenience
	'''
	if headers:
		return requests.session(auth=AUTH, headers=headers)
	else:
		return requests.session(auth=AUTH)


def get_data(key, params=None, data=None):
	'''
	Get data from API. See list of keys in the api function in
	this document.

	params: A dictionary that will be urlencoded

	Returns a dictionary.
	'''
	with session() as r:
		if params:
			response = r.get(api(key, params), data=data)
		else:
			response = r.get(api(key), data=data)

		content = response.content
		if response.ok:
			json = simplejson.loads(content)
			return json
		else:
			exit("Please verify your login credentials...")



def get_data_dict(apikey, datakey, dataValue):
	'''
	Output the dicionary of a specific datakey (such as 'name') with a
	value (such as 'My Weekend Project' for a given apikey 
	(such as 'projects')
	'''
	data = get_data(apikey)["data"]
	dump = simplejson.dumps(data, indent=2)

	# Data is an array of dicts. See if we find our datakey. If so,
	# return it. If not, return false.
	
	for x in data:
		if x[datakey].lower() == dataValue.lower():
			return x
	return False

def test_api(key, params=None, data=None):
	'''
	Output API info. Output wrapper for get_data
	'''
	print simplejson.dumps(get_data(key, params, data), indent=2)


def get_latest_time_entries():
	'''
	Gets the latest time entries. Returns a dictionary
	'''
	url = api("time_entries")
	with session() as r:
		content = r.get(url).content
		jsonDict = simplejson.loads(content) 
		return jsonDict

def new_time_entry(description):
	''' 
	Creates a new time entry. Pass in a description string.
	'''

	# Get the project ID of the client/project pair specified in 
	# .toggl_project. Make sure it's valid now before they start the timer
	# or they'll waste time in the event it's invalid
	try:
		projectID = get_project()["id"]
	except TypeError:
		if "CLIENT" in TOGGL.keys():
			print "The project " + TOGGL["PROJECT"]+" under the client " +\
			TOGGL["CLIENT"] + " was not found."
		else:
			print "The project " + TOGGL["PROJECT"] + " was not found"
		exit("Exiting...")
					


	# Get the current time and store it. Then pause until the user
	# says they are finished timing the task. Get the time they stopped
	# the timer, subtract it from the start_time, and store the difference
	# in seconds as the duration.
	#start_time = datetime.datetime.now()
	start_time = datetime.datetime.utcnow()
	local_start_time = datetime.datetime.now()

	# Let user know the timer has started, and wait for them to press
	# Enter to stop it.
	timer_start_print(description, local_start_time)

	try:
		raw_input()
	except (KeyboardInterrupt, SystemExit):
		exit("Task cancelled. Exiting")

	print "Sending data..."

	end_time = datetime.datetime.utcnow()
	time_difference = (end_time - start_time).seconds


	# Data passed to the request
	data = {"time_entry":{
			"duration": time_difference,
			"start": start_time.isoformat(),
			"stop": "null",
			"created_with": "Python Command Line Client",
			"project": {"id":projectID},
			"description": description}}
	url = api("time_entries")
	#url = "http://httpbin.org/post"

	headers = {"Content-Type": "application/json"}

	# JSON Encode the data dict
	data=simplejson.dumps(data)
	with session(headers=headers) as r:
		response = r.post(url, data=data)
		#print response.content
		print "Success."

def dashes(string):
	'''
	Return a string of dashes the length of string. Just for pretty 
	formatting
	'''
	return "-" * len(string)

def print_dict(theDict, indent=4):
	'''
	Outputs a dictionary all pretty like
	'''
	print simplejson.dumps(theDict, indent=indent)

def parse_file(fileLoc):
	'''
	Return a list containing the lines of the file.
	Ignore commented lines (lines beginning with #)

	fileLoc: location of the file as a string
	'''
	handle = open(fileLoc)

	# We'll be returning this list.
	returnList = []

	for line in handle:
		li = line.strip()

		# Ignore empty lines and comments
		if li and not li.startswith("#"):
			returnList.append(li)
	return returnList

def get_settings_from_file(keyList, fileLoc, theDict):
	'''
	parses file at fileLoc and searches for key:value pairs specified
	by keyList.

	Alters theDict dictionary 
	'''
	fileContents = parse_file(fileLoc)
	for line in fileContents:
		# Store the key value pair. Uppercase Key since it will be 
		# used in a global variable
		tmp = line.split(":")
		key = tmp[0].strip().upper()

		# Only append the key value pair if the key is found.
		if key in keyList:
			value = tmp[1].strip()
			theDict[key] = value

def timer_start_print(description, time):
	'''
	Print a message to let the user know that the timer has started
	and how to stop it
	'''
	print ""
	print "Task: " + description
	print "Project: " + TOGGL["PROJECT"]
	if "CLIENT" in TOGGL.keys():
		print "Client: " + TOGGL["CLIENT"]

	print time.strftime("Started at: %I:%M%p")
	print dashes(PROMPT + description)
	print "Press Enter to stop timer... (CTRL-C to cancel)"
	
def get_project():
	'''
	Get the dictionary of the project specified in the .toggl_project file.
	Will attempt to account for missing TOGGL["CLIENT"] key
	'''
	if "CLIENT" in TOGGL.keys():
		# It's stored Client - Project under the API
		tmp = TOGGL["CLIENT"] +" - "+ TOGGL["PROJECT"]
		project = get_data_dict("projects", "client_project_name", tmp)
	else:
		project = get_data_dict("projects", "name", TOGGL["PROJECT"])
	
	return project

# Get the global variables and settings.
from global_vars import *