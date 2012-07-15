import os
import pickle
import rosteraccess
import settings
from PyQt4.QtCore import QObject
from models import *

class DataStore(QObject):
    def __init__(self):
        # Load pickles or create fresh if no pickle file
        try:
            with open("DataStore.pickle", "rb") as f:
                unpickler = pickle.Unpickler(f)
                self.people = unpickler.load()
                self.clockedIn = unpickler.load()
                self.timeLog = unpickler.load()
            print("Loaded %d people (%d clocked in) and %d time entries." %
                    (len(self.people), len(self.clockedIn), len(self.timeLog)))
            for record in self.clockedIn.values():
                record.completed.connect(self.handle_signout)
        except (IOError, EOFError):
            self.people = {}
            self.timeLog = []
            self.clockedIn = {}

    def save(self):
        with open("DataStore.pickle", "wb") as f:
            pickler = pickle.Pickler(f)
            pickler.dump(self.people)
            pickler.dump(self.clockedIn)
            pickler.dump(self.timeLog)

    def handle_signout(self):
        record = self.sender()
        print("handling %d signing out" % record.id)
        record = self.clockedIn.pop(record.id, None)
        if record is not None:
            self.timeLog.append(record)

    def signInOut(self, id):
        """Sign person in or out (based on their current state).
        Returns False if person was previously signed in."""
        person = self.people[id]
        record = self.clockedIn.pop(id, None)
        if record is not None:
            # signing out
            record.signOut()
            self.timeLog.append(record)
            return False
        else:
            # signing in
            record = TimeRecord(person)
            record.completed.connect(self.handle_signout)
            self.clockedIn[id] = record
            return True

    def clearAll(self):
        """Clear all clocked in entries.  They will be saved in the time log
        but with no hours credit."""
        while self.clockedIn:
            record = self.clockedIn.popitem()[1]
            record.clear()
            self.timeLog.append(record)

    def signOutAll(self):
        """Sign out all clocked in entries."""
        while self.clockedIn:
            record = self.clockedIn.popitem()[1]
            record.signOut()
            self.timeLog.append(record)

    def sync(self):
        # Update people from roster
        try:
            for person in rosteraccess.getPersonList():
                if person.id in self.people:
                    self.people[person.id].updateFrom(person)
                else:
                    self.people[person.id] = person
        except IOError as e:
            # Unlikely we'll be able to do anything else
            print("Could not contact server to synchronize: %s" % e)
            return e

        # Download photos as necessary
        for person in self.people.values():
            size = 0
            if person.photo:
                try:
                    size = os.stat(person.photo).st_size
                except OSError:
                    pass
            if size != person.photoSize:
                try:
                    rosteraccess.getBadgePhoto(person.photoRemote, person.photo)
                except IOError as e:
                    print("Failed when downloading %s: %s" % (person.photo, e))

        # Push saved time log to server
        if not self.timeLog:
            return True
        try:
            print("Pushing %d time entries" % len(self.timeLog))
            ok = rosteraccess.putTimeRecords(self.timeLog)
        except IOError as e:
            print("Failed to push time entries: % s" % e)
            return e
        self.timeLog = [v for i, v in enumerate(self.timeLog) if i not in ok]
        return None

if __name__ == "__main__":
    import getpass
    settings.LOGIN_PASSWORD = getpass.getpass("Password: ")
    store = DataStore()
    store.sync()
    #person = list(store.people.keys())[0]
    #print("person %d" % person)
    #store.signInOut(person) # sign in
    #store.signInOut(person) # sign out
    #store.signInOut(person) # sign in
    #store.signOutAll()      # sign out
    #store.signInOut(person) # sign in
    #store.clearAll()        # clear
    store.save()