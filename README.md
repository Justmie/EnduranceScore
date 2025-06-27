# EnduranceScore
Get Garmin Endurancescore into intervals.icu

Provided as is. No support, if it breaks something, it's your own responsibility.

pip3 install garminconnect garth requests readchar

Commandline options: (No commandline: Only process today)\
--days \<number of days to fetch\> &emsp;(Number of past days to process)  eg: --days 180\
--dry-run &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;(Only fetch data and print, do not upload)

First use --dry-run to test if it works for you. Then use --days <number of days> to fetch your Endurance Score history.\
After the initial get use something like cron to run the script automatically every day.

On the intervals.icu website go to Activities -> Options -> Wellness\
Add the field: "Endurance Score"

In your Activities calander this will look something like this (with 5088 being the endurance score for that day).\
![image](https://github.com/user-attachments/assets/15390a35-18d9-404b-b78a-1e4f27a2d0dd)

Then in the "Compare" section of Intervals.icu add a custom graph:\
![image](https://github.com/user-attachments/assets/dca49098-956d-4ca0-80ba-7a0e462ba237)

Then your graph will look something like this:\
![image](https://github.com/user-attachments/assets/1fe27449-abc0-46ab-9ca4-e1a8ca79cced)


### Credits:

Cyberjunky for making the Pyhton-garminconnect API wrapper to make it possible to get data from Garmin Connect.
See: https://github.com/cyberjunky/python-garminconnect
