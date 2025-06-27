# EnduranceScore
Get Garmin Endurancescore into intervals.icu

Provided as is. No support, if it breaks something, it's your own responsibility.

pip3 install garminconnect garth requests readchar

Use something like cron to run the script automatically every day.

On the intervals.icu website go to Activities -> Options -> Wellness
Add the field: "Endurance Score"

Credits:

Cyberjunky for making the Pyhton-garminconnect API wrapper to make it possible to get data from Garmin Connect.
See: https://github.com/cyberjunky/python-garminconnect
