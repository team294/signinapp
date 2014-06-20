from __future__ import print_function
import os
import pickle
import backend_roster as backend
from PyQt4.QtCore import QObject, QMutex, QMutexLocker, pyqtSignal
from models import *

class DataStore(QObject):
    statusUpdate = pyqtSignal(str)
    statsChanged = pyqtSignal()

    def __init__(self, backend):
        super(DataStore, self).__init__()
        self.backend = backend
        self.mutex = QMutex(QMutex.Recursive)
        self.people = {}
        self.timeLog = []
        self.clockedIn = {}
        self.badgeToId = {}

    def load(self):
        # Load pickles or create fresh if no pickle file
        with QMutexLocker(self.mutex):
            try:
                with open("DataStore.pickle", "rb") as f:
                    unpickler = pickle.Unpickler(f)
                    self.people = unpickler.load()
                    self.clockedIn = unpickler.load()
                    self.timeLog = unpickler.load()
                self.statusUpdate.emit(
                        "Loaded %d people (%d clocked in) and %d time records." %
                        (len(self.people), len(self.clockedIn),
                         len(self.timeLog)))
                for record in self.clockedIn.values():
                    record.completed.connect(self.handle_signout)
                for person in self.people.values():
                    self.badgeToId[person.badge] = person.id
            except (IOError, EOFError):
                self.people = {}
                self.timeLog = []
                self.clockedIn = {}
                self.badgeToId = {}
            self.statsChanged.emit()

    def save(self):
        with QMutexLocker(self.mutex):
            with open("DataStore.pickle", "wb") as f:
                pickler = pickle.Pickler(f)
                pickler.dump(self.people)
                pickler.dump(self.clockedIn)
                pickler.dump(self.timeLog)

    def getNumPeople(self):
        with QMutexLocker(self.mutex):
            return len(self.people)

    def getNumTimeEntries(self):
        with QMutexLocker(self.mutex):
            return len(self.timeLog)

    def getNumClockedIn(self):
        with QMutexLocker(self.mutex):
            return len(self.clockedIn)

    def handle_signout(self):
        record = self.sender()
        id = record.person.id
        print("handling %d signing out" % id)
        with QMutexLocker(self.mutex):
            record = self.clockedIn.pop(id, None)
            if record is not None:
                self.timeLog.append(record)
            self.statsChanged.emit()

    def signInOut(self, badge):
        """Sign person in or out (based on their current state).
        Returns None if person was previously signed in,
        otherwise returns created TimeRecord."""
        with QMutexLocker(self.mutex):
            id = self.badgeToId[badge]
            person = self.people[id]
            record = self.clockedIn.pop(id, None)
            if record is not None:
                # signing out
                record.signOut()
                self.timeLog.append(record)
                self.save()
                self.statsChanged.emit()
                return None
            else:
                # signing in
                record = TimeRecord(person)
                record.completed.connect(self.handle_signout)
                self.clockedIn[id] = record
                self.save()
                self.statsChanged.emit()
                return record

    def clearAll(self):
        """Clear all clocked in records.  They will be saved in the time log
        but with no hours credit."""
        with QMutexLocker(self.mutex):
            while self.clockedIn:
                record = self.clockedIn.popitem()[1]
                record.clear()
                self.timeLog.append(record)
            self.save()
            self.statsChanged.emit()

    def signOutAll(self):
        """Sign out all clocked in records."""
        with QMutexLocker(self.mutex):
            while self.clockedIn:
                record = self.clockedIn.popitem()[1]
                record.signOut()
                self.timeLog.append(record)
            self.save()
            self.statsChanged.emit()

    def sync(self):
        # Update people from backend
        try:
            newpeople = self.backend.getPersonList()
            with QMutexLocker(self.mutex):
                self.badgeToId = {}
                for person in newpeople:
                    if person.id in self.people:
                        self.people[person.id].updateFrom(person)
                    else:
                        self.people[person.id] = person
                    self.badgeToId[person.badge] = person.id
        except IOError as e:
            # Unlikely we'll be able to do anything else
            self.statusUpdate.emit("Could not contact server to synchronize: %s" % e)
            return

        # Download photos as necessary
        for person in newpeople:
            size = 0
            if person.photo:
                try:
                    size = os.stat(person.photo).st_size
                except OSError:
                    pass
            if person.photoRemote and size != person.photoSize:
                self.statusUpdate.emit("Downloading %s" % person.photoRemote)
                try:
                    self.backend.getBadgePhoto(person.photoRemote, person.photo)
                except IOError as e:
                    self.statusUpdate.emit("Failed when downloading %s: %s" %
                            (person.photo, e))

        # Push saved time log to server
        with QMutexLocker(self.mutex):
            if self.timeLog:
                try:
                    self.statusUpdate.emit("Pushing %d time records" %
                            len(self.timeLog))
                    ok = self.backend.putTimeRecords(self.timeLog)
                except IOError as e:
                    self.statsChanged.emit()
                    self.statusUpdate.emit("Failed to push time records: %s" % e)
                    return
                self.timeLog = [v for i, v in enumerate(self.timeLog) if i not in ok]
                self.statusUpdate.emit("Pushed %d time records" % len(ok))
            else:
                self.statusUpdate.emit("Synchronization complete")

            self.statsChanged.emit()

if __name__ == "__main__":
    try:
        from configparser import ConfigParser
    except ImportError:
        from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read("settings.ini")
    import getpass

    from backend_roster import Backend
    backend = Backend(config)
    backend.setPassword(getpass.getpass("Password: "))
    store = DataStore(backend)
    store.statusUpdate.connect(print)
    store.load()
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
