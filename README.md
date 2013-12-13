SignInApp
=========

A sign in application designed to interface to CSV files or the Roster
web application.

Requirements
------------

- Python (2 or 3)
- PyQt4

CSV Backend Configuration
-------------------------

Edit people.csv to add your team members.  Column meanings:
- ID: any numeric value.  Needs to be unique (recommend incrementing values)
- Name: person's name that should appear and/or be searchable
- Student: A value such as "false", "no", or "0" will cause the team member
  to be seen as a mentor or parent instead of a student.
- Photo Path: Path to a jpg file shown as the user's picture.  The path can
  be either absolute or relative; photos will be copied to the photos/
  directory.
- Badge Number: If not blank, overrides ID for sign-in purposes.

"Synchronization" will result in writing to the records.csv file.  Columns are:
- ID: person's ID
- Name: person's name (copied from people.csv value)
- Student: person's student status (copied from people.csv value)
- Event: placeholder for adding records manually; SignInApp leaves this blank.
- Clocked In: Date/Time clocked in (local timezone)
- Clocked Out: Date/Time clocked out (local timezone)
- Hours: Hours recorded (may be zero if person "cleared" instead of signed out)
- Recorded: Date/Time hours were recorded (e.g. signed out or cleared)

Roster Backend Configuration
----------------------------

Edit settings.ini to change BACKEND to "roster" and set the BASE\_URL and
LOGIN\_USERNAME appropriately.
Due to security concerns, we recommend NOT setting the LOGIN\_PASSWORD and
using a dedicated user for LOGIN\_USERNAME.
The other settings shouldn't need tweaking unless you have a very customized
Roster application setup.

