#!/usr/bin/python
#
# Copyright (c) 2011 //SEIBERT/MEDIA GmbH
#
# written by: Torsten Rehn <trehn@seibert-media.net>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import email.parser
import poplib
import smtplib
import sys

# change these:

INCOMING_HOST = "pop3.example.com"
INCOMING_USER = "zendesk2highrise@example.com"
INCOMING_PASS = "whoopdidoo"

OUTGOING_HOST = "smarthost.example.com"
OUTGOING_EMAIL = "dropbox@12345678.example.highrisehq.com"

DEBUG_EMAIL = "root@example.com"

# you shouldn't need to change anything below

MAGIC_TOKEN = "/deal"
DEBUG = True

def debug_log(msg):
	if DEBUG is True:
		print "DEBUG: " + msg

def handle_outgoing_mail(sender, body):
	debug_log("sending email message")
	smtpconn = smtplib.SMTP(OUTGOING_HOST)
	if DEBUG:
		smtpconn.set_debuglevel(1)
		smtpconn.sendmail(sender, DEBUG_EMAIL, body)
	else:
		smtpconn.sendmail(sender, OUTGOING_EMAIL, body)
	smtpconn.quit()
	debug_log("email sent")

def handle_incoming_mail(lines):
	from_line = ""
	subject_line = ""
	# Yes, this is inefficient. No, I don't care.
	for line in lines:
		if line.startswith("From: "):
			debug_log(line)
			from_line = line
			break
	for line in lines:
		if line.startswith("Subject: "):
			debug_log(line)
			subject_line = line
			break
	for line in lines:
		if line.startswith("Date: "):
			debug_log(line)
			break
	
	msg = email.parser.Parser().parsestr("\n".join(lines))
	content = None
	for part in msg.walk():
		if part.get_content_type() == "text/plain":
			content = part.get_payload(decode = True)
			break
	if content is None:
		debug_log("message has no plaintext part, skipping")
		return
	
	encountered_magic_token = False
	output_lines = [from_line,
	                "To: <" + OUTGOING_EMAIL + ">",
	                subject_line]
	for line in content.split("\n"):
		if not encountered_magic_token:
			if line.startswith(MAGIC_TOKEN):
				encountered_magic_token = True
		if encountered_magic_token:
			output_lines.append(line)
			
	if not encountered_magic_token:
		debug_log("message has no magic token, skipping")
		return
	
	output_body = "\n".join(output_lines)
	
	handle_outgoing_mail(msg["From"], output_body)

if __name__ == "__main__":
	if len(sys.argv) > 1:
		if sys.argv[1] == "--cron":
			DEBUG = False 
	
	if DEBUG is True:
		answer = raw_input("Run script in debug mode (emails will be sent to " + DEBUG_EMAIL + ")? [y/N] ")
		if answer != "Y" and answer != "y":
			print "exiting, run script with --cron to use production settings"
			sys.exit(0)
	
	debug_log("initiating POP3 connection to " + INCOMING_HOST)
	pop3conn = poplib.POP3(INCOMING_HOST)
	debug_log("authenticating as " + INCOMING_USER)
	pop3conn.user(INCOMING_USER)
	pop3conn.pass_(INCOMING_PASS)
	number_of_messages = len(pop3conn.list()[1])
	debug_log("found " + str(number_of_messages) + " messages")
	for i in range(number_of_messages):
		debug_log("processing message #" + str(i + 1))
		handle_incoming_mail(pop3conn.retr(i + 1)[1])
		pop3conn.dele(i + 1)
	pop3conn.quit()
