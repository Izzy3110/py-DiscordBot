from __future__ import unicode_literals

import base64
from datetime import datetime
import imaplib
import os
import email
import time
import json


class Time(object):
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    )

    def display_time(self, seconds, granularity=2):
        result = []

        for name, count in self.intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])


class Mail(object):
    filter_results = None

    email_host = "imap.gmx.net"
    email_account = "sascha.frank.88@gmx.de"
    email_password = os.environ["APP_PASSWORD"]

    filter = {
        "from": "support@hetzner.com,server-order@hetzner.com,noreply@hetzner.com"
    }

    already_tracked_ids = []

    def __init__(self):
        self.mail = imaplib.IMAP4_SSL(self.email_host)
        self.unseen_mails = {}

    def login(self):
        try:
            self.mail.login(self.email_account, os.environ["APP_PASSWORD"])
        except imaplib.IMAP4.error as imap_err:
            error_message = str(imap_err).lstrip('b\'').rstrip("'")
            if error_message == "authentication failed":
                print("ERR: wrong email/password")

    def shutdown(self):
        self.mail.close()
        self.mail.shutdown()

    @staticmethod
    def parse_email_date(date):
        message_object = {
            "date": {

            }
        }
        date_tuple = email.utils.parsedate_tz(date)
        if date_tuple:
            local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            message_object["date"]["str"] = local_date.strftime("%d.%m.%Y %H:%M:%S")
            mail_timestamp = time.mktime(
                datetime.strptime(message_object["date"]["str"], "%d.%m.%Y %H:%M:%S").timetuple()
            )
            seconds_ago = int(time.time() - mail_timestamp)
            human_time_ago = Time().display_time(seconds_ago)
            local_message_date = "%s" % (str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))

            message_object["date"]["human_ago"] = human_time_ago
            message_object["date"]["local_message"] = local_message_date
            return message_object

    def get_unseen_messages(self):
        self.filter_results = {}
        self.unseen_mails = {}
        self.mail.list()
        self.mail.select('INBOX')

        if self.mail.uid('search', None, "UNSEEN")[0] == "OK":
            result, data = self.mail.uid('search', None, "UNSEEN")

            i = len(data[0].split())
            if i > 0:
                message_is_filtered = False
                for x in range(i):
                    mail_ = {
                        "from": "",
                        "to": "",
                        "subject": "",
                        "message": {
                            "base64": ""
                        }
                    }
                    latest_email_uid = data[0].split()[x]
                    latest_email_uid_ = int(latest_email_uid.decode())
                    if not latest_email_uid_ in self.already_tracked_ids:
                        self.already_tracked_ids.append(latest_email_uid_)
                        result, email_data = self.mail.uid('fetch', latest_email_uid, '(RFC822)')
                        if result == "OK":
                            raw_email = email_data[0][1]
                            raw_email_string = raw_email.decode('utf-8')
                            email_message = email.message_from_string(raw_email_string)
                            mail_["message"]["base64"] = base64.b64encode(raw_email).decode()
                            date_data = self.parse_email_date(email_message['Date'])
                            for k in date_data:
                                if k not in mail_.keys():
                                    mail_[k] = date_data[k]

                            mail_["from"] = str(email.header.make_header(email.header.decode_header(email_message['From'])))

                            contains = False
                            for email_from_filter_address in self.filter["from"].split(","):
                                if email_from_filter_address in mail_["from"] and not contains:
                                    contains = True
                                    """
                                    print("contains filtered substring: "+str(contains))
                                    print(email_from_filter_address)
                                    print("")
                                    """

                            if contains:
                                message_is_filtered = True

                            mail_["to"] = str(email.header.make_header(email.header.decode_header(email_message['To'])))
                            mail_["subject"] = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
                        else:
                            mail_[str(latest_email_uid_)] = "error fetching mail"

                        self.unseen_mails[str(latest_email_uid_)] = mail_
                        if message_is_filtered:
                            self.filter_results[str(latest_email_uid_)] = mail_

                    # else:
                    #     print("already processed")
            return self.unseen_mails


Mail_ = Mail()
Mail_.login()
try:
    while True:
        messages = Mail_.get_unseen_messages()
        # All unseen - print(json.dumps(messages, indent=4))
        print(json.dumps(Mail_.filter_results,indent=4))
        time.sleep(7)
except KeyboardInterrupt:
    print("shutting down!")
finally:
    Mail_.shutdown()
