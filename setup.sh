#!/bin/bash
sudo pip install vobject pytz
sudo chmod +x start.sh
printf '{\n"minutesBetweenFetches" : 30,\n"timezone" : "Europe/Madrid",\n"hourFormat" : 12,\n"calendar" : "HTTP_GOOGLE_CALENDAR_SECRET_ADDRESS_HERE"\n}' > ./config.json
