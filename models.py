from __future__ import print_function
from datetime import datetime
import os
from PyQt4.QtCore import QObject, pyqtSignal

class SuperQObject(QObject):
    """ Permits the use of super() in class hierarchies that contain QObject.

    Unlike QObject, SuperQObject does not accept a QObject parent. If it did,
    super could not be emulated properly (all other classes in the hierarchy
    would have to accept the parent argument--they don't, of course, because
    they don't inherit QObject.)
    """

    def __new__(cls, *args, **kw):
        # We initialize QObject as early as possible. Without this, Qt complains
        # if SuperQObject is not the first class in the super class list.
        inst = QObject.__new__(cls)
        QObject.__init__(inst)
        return inst

    def __init__(self, *args, **kw):
        # Emulate super by calling the next method in the MRO, if there is one.
        mro = self.__class__.mro()
        for qt_class in QObject.mro():
            mro.remove(qt_class)
        next_index = mro.index(SuperQObject) + 1
        if next_index < len(mro):
            mro[next_index].__init__(self, *args, **kw)

class Person(SuperQObject):
    updated = pyqtSignal()

    def __init__(self, id, name, student, photoPath, photoSize, badge):
        super(Person, self).__init__()
        self.id = id
        self.name = name
        self.student = student
        self.photo = "photos/"+photoPath.split('/')[-1]
        self.photoRemote = photoPath
        self.photoSize = photoSize
        self.badge = badge

    def __reduce__(self):
        return (Person, (self.id, self.name, self.student, self.photoRemote, self.photoSize, self.badge))

    def updateFrom(self, other):
        assert(self.id == other.id)
        changed = (self.name != other.name or
                self.student != other.student or
                self.photo != other.photo or
                self.photoRemote != other.photoRemote or
                self.photoSize != other.photoSize or
                self.badge != other.badge)
        self.name = other.name
        self.student = other.student
        self.photo = other.photo
        self.photoRemote = other.photoRemote
        self.photoSize = other.photoSize
        self.badge = other.badge
        if changed:
            self.updated.emit()

    def hasPhoto(self):
        if self.photoSize == 0:
            return False
        try:
            size = os.stat(self.photo).st_size
        except OSError:
            return False
        return size == self.photoSize

    def __repr__(self):
        return 'Person(%s, %s, %s, %s, %s, %s)' % \
                (repr(self.id), repr(self.name), repr(self.student),
                 repr(self.photoRemote), repr(self.photoSize), repr(self.badge))

    def __str__(self):
        return "%s (%d)" % (self.name, self.badge)

class TimeRecord(SuperQObject):
    completed = pyqtSignal()

    def __init__(self, person):
        super(TimeRecord, self).__init__()
        self.person = person
        self.inTime = datetime.now()
        self.outTime = None
        self.hours = 0.0
        self.recorded = None
        print("%s signed in" % self.person)

    def __reduce__(self):
        return (TimeRecord, (self.person,),
                {'inTime': self.inTime,
                    'outTime': self.outTime,
                    'hours': self.hours,
                    'recorded': self.recorded})

    def signOut(self):
        print("%s signing out" % self.person)
        if self.recorded is not None:
            print("already recorded")
            return
        self.outTime = datetime.now()
        self.hours = round((self.outTime - self.inTime).total_seconds() / 3600.0, 2)
        self.recorded = datetime.now()
        self.completed.emit()

    def clear(self):
        print("%s cleared" % self.person)
        if self.recorded is not None:
            print("already recorded")
            return
        self.outTime = self.inTime
        self.hours = 0.0
        self.recorded = datetime.now()
        self.completed.emit()

