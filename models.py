from datetime import datetime

class Person:
    def __init__(self, id, name, student, photoPath, photoSize):
        self.id = id
        self.name = name
        self.student = student
        self.photo = "photos/"+photoPath.split('/')[-1]
        self.photoRemote = photoPath
        self.photoSize = photoSize

    def __str__(self):
        return "%s (%s) [%s]" % \
                (self.name, self.id, "student" if self.student else "adult")

class TimeRecord:
    def __init__(self, person):
        self.person = person.id
        self.inTime = datetime.now()
        self.outTime = None
        self.hours = 0.0
        self.recorded = None

    def signOut(self):
        self.outTime = datetime.now()
        self.hours = (self.outTime - self.inTime).total_seconds() / 3600.0
        self.recorded = datetime.now()

    def clear(self):
        self.outTime = datetime.now()
        self.hours = 0.0
        self.recorded = datetime.now()

