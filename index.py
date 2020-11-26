import os
import signal
import json
import vobject # pip install vobject
import csv
import pytz # pip install pytz
import webbrowser
import re
import json

from datetime import datetime
from urllib2 import Request
#from urllib2.error import URLError
from urllib2 import urlopen

from gi.repository import Gtk as gtk, GLib
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

config = json.load(open('./config.json'))

class CalendarEvent(object):
    def __init__(self, date, component):
        self.date = date
        self.component = component

class CalendarIndicator(object):

    def __init__(self):
        self.APPINDICATOR_ID = 'calendar-indicator'
        self.meetUrl = False

        self.indicator = appindicator.Indicator.new(self.APPINDICATOR_ID, "", appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_label("Reading calendar...", "8.8")
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        notify.init(self.APPINDICATOR_ID)
        self.readEvents()
        GLib.timeout_add_seconds(config["minutesBetweenFetches"] * 60, self.readEvents)
        gtk.main()

    def readEvents(self):
        data = urlopen(config["calendar"]).read().decode('utf-8')
#        data = open("calendar.ics").read() # useful for debugging
        localTZ = pytz.timezone(config["timezone"])
        now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(localTZ)
        nearestEvent = False
        meetsPattern = "(https://meet.google.com/[a-zA-Z0-9_-]+)"

        if (config["hourFormat"] == 24):
            hourFormat = "%H:%M"
        else :
            hourFormat = "%I:%M %p"

        # find the most immediate event
        for cal in vobject.readComponents(data):
            for component in cal.components():
                if component.name != "VEVENT":
                    continue

                try:
                    eventDate = component.dtstart.valueRepr().replace(tzinfo=pytz.utc).astimezone(localTZ)
                except:
                    print("Invalid date, skipping event " + component.summary.valueRepr())
                    continue

                # Repeating events are somehow special, they don't tell you if today meets the criteria, so you gotta adapt
                # RRULE format: FREQ=WEEKLY;UNTIL=20200318T225959Z;BYDAY=FR,MO,TH,TU,WE
                if  hasattr(component, 'rrule'):
                    allEventDates = component.getrruleset(addRDate=True)
                    expectedDate = allEventDates[0].replace(day=now.day, month=now.month, year=now.year); # ugly hack to keep proper event hour/minute while checking if happens today too

                    if expectedDate in allEventDates:
                        eventDate = expectedDate

                if eventDate > now and eventDate.day == now.day and (nearestEvent == False or eventDate < nearestEvent.date):
                    nearestEvent = CalendarEvent(eventDate, component)


        if (nearestEvent == False):
            self.indicator.set_label("No more events for today! :P", "8.8")
        else:
            hasMeetUrl = re.search(meetsPattern, nearestEvent.component.description.valueRepr())

            if (hasMeetUrl):
                self.meetUrl = hasMeetUrl.group()
            else :
                self.meetUrl = False

            self.indicator.set_label("Today at " + nearestEvent.date.strftime(hourFormat) + " -> " + nearestEvent.component.summary.valueRepr(), "8.8")


        return True # required for timeout_add_seconds to work

    def build_menu(self):
        menu = gtk.Menu()

        item = gtk.MenuItem('Open Google Meet')
        item.connect('activate', self.openMeet)
        menu.append(item)

        item = gtk.MenuItem('Open Google Calendar')
        item.connect('activate', self.openCalendar)
        menu.append(item)

        item = gtk.MenuItem('Refresh')
        item.connect('activate', self.refresh)
        menu.append(item)

        item = gtk.MenuItem('Quit')
        item.connect('activate', self.quit)
        menu.append(item)

        menu.show_all()
        return menu

    def openMeet(self, _):
        if (self.meetUrl):
            webbrowser.open(self.meetUrl, new=2)
        else :
            notify.Notification.new("Error", "Failed to find a link for Google Meets in this event", None).show()

    def openCalendar(self, _):
        webbrowser.open('https://calendar.google.com', new=2)

    def refresh(self, _):
        self.indicator.set_label("Reading calendar...", "8.8")
        self.readEvents()

    def quit(self, _):
        notify.uninit()
        gtk.main_quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    calendarIndicator = CalendarIndicator()
