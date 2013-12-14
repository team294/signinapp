import csv
import os
from models import *

class Backend:
    def __init__(self, config):
        self.config = config

    def get_setting(self, name):
        return self.config.get('csv', name)

    def getPersonList(self):
        with open(self.get_setting('PEOPLE_FILE'), "rt") as f:
            people = []
            for row in csv.DictReader(f):
                id = int(row["ID"])
                name = row["Name"]
                student = (row["Student?"].lower() != "false" and
                        row["Student?"].lower() != "no" and
                        row["Student?"] != "0")
                photoPath = row["Photo Path"]
                try:
                    photoSize = os.stat(photoPath).st_size
                except OSError:
                    photoSize = 0
                people.append(Person(id, name, student, photoPath, photoSize, id))
            return people

    def getBadgePhoto(self, photoPath, localName):
        # Avoid copy if both are the same file
        if os.path.abspath(photoPath) == os.path.abspath(localName):
            return
        with open(photoPath, "rb") as f:
            data = f.read()
        with open(localPath, "wb") as f:
            f.write(data)

    def putTimeRecords(self, records):
        if not records:
            return set() # no records to put

        with open(self.get_setting('RECORDS_FILE'), "a") as f:
            writer = csv.writer(f)
            for record in records:
                writer.writerow([record.person.id, record.person.name,
                        record.person.student, "", record.inTime,
                        record.outTime, record.hours, record.recorded])

            # report all as successfully added
            return set(i for i, v in enumerate(records))
