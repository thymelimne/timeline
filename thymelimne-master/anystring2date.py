#!/usr/bin/env python
# coding: utf-8

# In[1]:


import datetime
import re
from calendar import month_name


# In[2]:


def stripweekday(string):
	string = string.lower()
	
	string = re.sub("sunday","",string)
	string = re.sub("monday","",string)
	string = re.sub("tuesday","",string)
	string = re.sub("wednesday","",string)
	string = re.sub("thursday","",string)
	string = re.sub("friday","",string)
	string = re.sub("saturday","",string)
	
	string = re.sub("sun","",string)
	string = re.sub("mon","",string)
	string = re.sub("tues","",string)
	string = re.sub("tue","",string)
	string = re.sub("wed","",string)
	string = re.sub("thurs","",string)
	string = re.sub("thur","",string)
	string = re.sub("thu","",string)
	string = re.sub("fri","",string)
	string = re.sub("saturday","",string)
	
	return string


# In[3]:

'''
# Copied from this: https://stackoverflow.com/questions/44197731/extract-month-name-from-raw-string
def extractmonth(s):
	months = {m.lower() for m in month_name[1:]}
	month = next((word for word in s.split() if word.lower() in months), None)
	string = re.sub(month, "", s)
	return month, string
'''
def extractmonth(string):
	tokens = string.split(' ')
	month = "January"
	for token in tokens:
		if token in month_name:
			month = token
	return month, string

# In[4]:


def month2number(month):
	mn = datetime.datetime.strptime(month,"%B").month
	return mn


# In[5]:


def getnumbers(string):
	return [int(s) for s in string.split() if s.isdigit()]


# In[6]:


def extractyear(numbers):
	for i in range(len(numbers)):
		number = numbers[i]
		if number>200: # Let's expect it to be after 200 A.D.
			return numbers.pop(i)
	return None


# In[29]:


# Should be simple:
def extractday(numbers):
	try:
		return numbers.pop(0)
	except:
		return None


# In[33]:


# Convert any string to a date object
def anystring2date(string):	
	print("DJFSDKLFJKLDS")
	print(string)
	print("JDFKLSDJFOVMIEO")
	if not isinstance(string, str):
		return None
	
	month, string = extractmonth(string)
	monthnumber = month2number(month)
	
	string = stripweekday(string)
	string = re.sub(",","",string)
	string = re.sub("[a-z]","",string)
	numbers = getnumbers(string)

	yearnumber = extractyear(numbers)
	if yearnumber==None: # has-year-or-not is the litmus test we'll go with to decide if it's a date or not.
		return None
	daynumber = extractday(numbers)

	if daynumber==None:
		daynumber=1 #default day.
	
	date = datetime.date(year=yearnumber, month=monthnumber, day=daynumber)
	return date


# In[9]:


#====================================


# In[37]:


# test it
if __name__=="__main__":
	string = "Monday, 25 December 1066"
	date = anystring2date(string, p=True)
	print(date)


# In[ ]:





# In[ ]:




