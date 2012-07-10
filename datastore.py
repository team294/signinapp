import os
import pickle
import rosteraccess
import settings
from models import *

class DataStore:
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

    def signInOut(self, id):
        """Sign person in or out (based on their current state).
        Returns False if person was previously signed in."""
        if id in self.clockedIn:
            # signing out
            entry = self.clockedIn.pop(id)
            entry.signOut()
            self.timeLog.append(entry)
            return False
        else:
            # signing in
            self.clockedIn[id] = TimeRecord(id)
            return True

    def clearAll(self):
        """Clear all clocked in entries.  They will be saved in the time log
        but with no hours credit."""
        for entry in self.clockedIn:
            entry.clear()
            self.timeLog.append(entry)
        self.clockedIn.clear()

    def signOutAll(self):
        """Sign out all clocked in entries."""
        for entry in self.clockedIn:
            entry.signOut()
            self.timeLog.append(entry)
        self.clockedIn.clear()

    def sync(self):
        # Update people from roster
        try:
            people = {}
            for person in rosteraccess.getPersonList():
                self.people[id] = person
            self.people = people
        except IOError as e:
            # Unlikely we'll be able to do anything else
            print("Could not contact server to synchronize: %s" % e)
            return e

        # Download photos as necessary
        for person in self.people:
            try:
                size = os.stat(photoLocal).st_size
            except OSError:
                size = 0
            if size != person.photoSize:
                try:
                    rosteraccess.getBadgePhoto(person.photoRemote, person.photo)
                except IOError as e:
                    print("Failed when downloading %s: %s" % (person.photo, e))

        # Push saved time log to server
        if not self.timeLog:
            return True
        try:
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
    store.save()
