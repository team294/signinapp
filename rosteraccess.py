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
import settings
from models import *

def login(loc = settings.BASE_LOCATION):
    login_url = settings.BASE_URL + settings.LOGIN_LOCATION
    cookies = HTTPCookieProcessor()
    opener = build_opener(cookies)
    opener.open(login_url)

    try:
        token = [x.value for x in cookies.cookiejar if x.name == 'csrftoken'][0]
    except IndexError:
        raise IOError("No csrf cookie found")

    params = dict(username=settings.LOGIN_USERNAME,
            password=settings.LOGIN_PASSWORD,
            next=loc,
            csrfmiddlewaretoken=token)
    encoded_params = urlparse.urlencode(params).encode('utf-8')

    req = Request(login_url, encoded_params)
    req.add_header('Referer', login_url)
    response = opener.open(req)
    if response.geturl() == login_url:
        raise IOError("Authentication refused")
    return opener, response

def fetchWithLogin(loc):
    return login(loc)[1].read()

def getPersonList():
    data = fetchWithLogin(settings.SIGNIN_PERSON_LIST_LOCATION).decode('utf-8')
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

def getBadgePhoto(photoPath, localName):
    print("downloading %s" % photoPath)
    urlretrieve(settings.BASE_URL + photoPath, localName)

def putTimeRecords(records):
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
        writer.writerow([record.person.id, "", record.inTime, record.outTime,
                record.hours, record.recorded])

    # send it
    opener = login()[0]
    url = settings.BASE_URL + settings.TIME_RECORD_BULK_ADD_LOCATION
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
    import getpass
    settings.LOGIN_PASSWORD = getpass.getpass("Password: ")
    people = list(getPersonList())
    for person in people:
        print(person.name)

    rec = TimeRecord(people[0])
    rec.clear()
    print("should be {0} ==> %s" % putTimeRecords([rec]))
