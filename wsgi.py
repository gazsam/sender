#!/usr/bin/env python

import re
import os
import sys
import time
import bottle
import logging
import urllib2
import urlparse
import contextlib
from messages import Message, MessageDB, MessageEncoder, MessageQueue

from bottle import route, request,get, post, put, delete, response, template


import json

STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')

logging.basicConfig()
log = logging.getLogger('receiver')
log.setLevel(logging.DEBUG)


log.debug("setting up message queue and db connection...")

mysql_url = urlparse.urlparse(os.environ['MYSQL_URL'])
rabbit_url = os.environ['RABBITMQ_URL']
queue_name = os.environ['QUEUE_NAME']

print os.environ['MYSQL_URL']
print os.environ['RABBITMQ_URL']

#rdb = redis.Redis(host=url.hostname, port=url.port, password=url.password)

url = mysql_url.hostname
password = mysql_url.password
user = mysql_url.username
dbname = mysql_url.path[1:] 


messageDB = MessageDB(url,dbname,user,password)
messageQueue = MessageQueue(rabbit_url, messageDB)
messageQueue.getMessagesAsync(queue_name)
    
@get('/receive') 
def getReceive():
    
    log.debug("handling /received path")

#     new_messages = messageQueue.getMessages()
#     
#     messageDB.addMessages(new_messages)
    
    all_messages = messageDB.getMessages()
    
    return json.dumps(all_messages,cls=MessageEncoder)

'''
view routes
'''

@route('/send/<number>')
def send(number=None):
	if not number:
		return template('Please add a number to the end of url: /send/5')
	fib = F(int(number))
	vcap_services = json.loads(os.environ['VCAP_SERVICES'])
	srv = vcap_services['RABBITMQ_URL']
	parameters = pika.URLParameters(srv['url'])
	connection = pika.BlockingConnection(parameters)
	channel = connection.channel()
	 
	channel.queue_declare(queue=queue_name)
	 
	channel.basic_publish(exchange='', routing_key='fibq', body=fib)
	connection.close()
	return template('Sent the Fibonacci number for {{number}}, {{fib}} in the fibq', number=number, fib=fib, srv=srv)

def F(n):
	if n == 0: return 0
	elif n == 1: return 1
	else: return F(n-1)+F(n-2)

@route('/')
@route('/fib/<number>')
def fib(number=None):
	if not number:
		return template('Please add a number to the end of url: /fib/5')
	fib = F(int(number))
	return template('The Fibonacci number for {{number}} is {{fib}}', number=number, fib=fib)


@route('/static/:filename')
def serve_static(filename):
    log.debug("serving static assets")
    return bottle.static_file(filename, root=STATIC_ROOT)

'''
service runner code
'''
log.debug("starting web server")
application = bottle.app()
application.catchall = False

"""
#UNCOMMENT BELOW FOR RUNNING ON LOCALHOST
if os.getenv('SELFHOST', False):

url = os.getenv('VCAP_APP_HOST')
port = int(os.getenv('VCAP_APP_PORT'))
bottle.run(application, host=url, port=port)

#UNCOMMENT BELOW FOR RUNNING ON HDP
"""

bottle.run(application, host='0.0.0.0', port=os.getenv('PORT', 8080))


# this is the last line
