# Python 2 and 3 compatibility
from __future__ import print_function
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
try:
    from urllib.request import (urlretrieve, HTTPCookieProcessor, build_opener,
            Request)
except ImportError:
    from urllib import urlretrieve
    from urllib2 import HTTPCookieProcessor, build_opener, Request
import io
import csv
from models import *

class Backend:
    def __init__(self, config):
        self.config = config

    def get_setting(self, name):
        return self.config.get('roster', name)

    def login(self, loc=None):
        if loc is None:
            loc = self.get_setting('BASE_LOCATION')
        login_url = self.get_setting('BASE_URL') + \
                self.get_setting('LOGIN_LOCATION')
        cookies = HTTPCookieProcessor()
        opener = build_opener(cookies)
        opener.open(login_url)

        try:
            token = [x.value for x in cookies.cookiejar if x.name == 'csrftoken'][0]
        except IndexError:
            raise IOError("No csrf cookie found")

        params = dict(username=self.get_setting('LOGIN_USERNAME'),
                password=self.get_setting('LOGIN_PASSWORD'),
                next=loc,
                csrfmiddlewaretoken=token)
        encoded_params = urlparse.urlencode(params).encode('utf-8')

        req = Request(login_url, encoded_params)
        req.add_header('Referer', login_url)
        response = opener.open(req)
        if response.geturl() == login_url:
            raise IOError("Authentication refused")
        return opener, response

    def fetchWithLogin(self, loc):
        return self.login(loc)[1].read()

    def getPersonList(self):
        data = self.fetchWithLogin(self.get_setting('SIGNIN_PERSON_LIST_LOCATION')).decode('utf-8')
        people = []
        for row in csv.DictReader(io.StringIO(data, newline="")):
            id = int(row["id"])
            name = row["name"]
            student = (row["student"] != "False")
            photoPath = row["photo"]
            photoSize = int(row["photo size"])
            badge = int(row["badge"])
            people.append(Person(id, name, student, photoPath, photoSize, badge))
        return people

    def getBadgePhoto(self, photoPath, localName):
        print("downloading %s" % photoPath)
        urlretrieve(self.get_setting('BASE_URL') + photoPath, localName)

    def putTimeRecords(self, records):
        """Send list of time records to server.  Returns set of indices of
        accepted records."""
        if not records:
            return # no records to put

        # build csv file to send
        f = io.StringIO(newline='')
        writer = csv.writer(f)
        writer.writerow(['person', 'event', 'clock_in', 'clock_out', 'hours',
                'recorded'])
        for record in records:
            writer.writerow([record.person.id, "", record.inTime,
                    record.outTime, record.hours, record.recorded])

        # send it
        opener = self.login()[0]
        url = self.get_setting('BASE_URL') + \
                self.get_setting('TIME_RECORD_BULK_ADD_LOCATION')
        data = f.getvalue().encode('utf-8')
        clen = len(data)
        req = Request(url, data,
                {'Content-Type': 'text/csv', 'Content-Length': clen})
        with opener.open(req) as response:
            if response.geturl() != url:
                raise IOError("Authentication refused")
            # response is a str() of a list, convert back into a real list
            resp = response.read().decode('utf-8').strip()
            ok, sep, errs = resp.partition('\n')
            if errs:
                print(errs)
            if ok == "[]": # handle empty list as the below doesn't
                return set()
            return set(int(x) for x in ok.strip("[]").split(','))

if __name__ == "__main__":
    try:
        from configparser import ConfigParser
    except ImportError:
        from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read("settings.ini")
    import getpass
    config.set('roster', 'LOGIN_PASSWORD', getpass.getpass("Password: "))

    backend = Backend(config)
    people = list(backend.getPersonList())
    for person in people:
        print(person.name)

    rec = TimeRecord(people[0])
    rec.clear()
    print("should be {0} ==> %s" % backend.putTimeRecords([rec]))
