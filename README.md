# calendar
DAKilla Family Calendar and Pictures

DAKilla is a free home calendar dashboard app, displaying any number of google calendars and rotating family pictures. DAKilla is a flask web site running on port 8000.
DAKilla is a free alternative to using DAKboards when you want to have multiple google calendars displayed.

create an images folder containing all the images you want to display in the calendar. create a file called ics_urls.txt and place it in a folder on your computer. The ics_urls.txt needs to contain one url per line like this:

https://calendar.google.com/calendar/ical/george.bush%40gmail.com/private-6c32453545663e44534e/basic.ics https://calendar.google.com/calendar/ical/joe.biden%40gmail.com/private-fdsfea08dd8c1c6f53f3/basic.ics

The ics_url.txt can contain multiple ICS urls place the file in a folder.

Now it is time to pull the DAKilla image: docker pull swedebear/dakilla

Next Run the image and specify the src path where you saved your images and ics file. Do not modify the target!

docker run -d --mount type=bind,src=/Users/userx/Documents/images,target=/calendar/static/images --mount type=bind,src=/Users/userx/Documents/ics,target=/calendar/static/ics --name calendarx -p 8000:8000 swedebear/dakilla:latest

Open your browser and navigate to your IP address or localhost:8000. It should now display the next 7 days of calendar events and rotating the images every minute.

Let me know how you like it dghovd@gmail.com
