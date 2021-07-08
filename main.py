# Author: Syed M Faizan
# Purpose: To search and book pfizer vaccine appointments
# How to use this script: Book any appointment (Pfizer or moderna doesn't matter). You will receive an email for appointment confirmation. This email got a button to view/reschedule/cancel the appointment. Copy the link of that button and use in this script.



import urllib.request
import json 
from datetime import datetime

# appointment link sent over email
EMAIL_LINK = "<EMAIL_LINK>"

# ESRI Geo Coordinates of location from where you want to search for appointments
TARGET_X = 453435.678
TARGET_Y = 4945093.515
# Maximum distance in meters from the above given GIS Coordinates to search within for appointments.
MAX_DISTANCE = 20000

# Upper limit of date time to search for appointments
TARGET_TIME = "2021-07-20T23:59:00.000Z"




def rescheduleAppointment(appointmentID, targetAppointment):
    rescheduleLink = "https://sync-cf2-1.canimmunize.ca/fhir/v1/public/appointment/"+appointmentID+"/reschedule"
    data = { 'target': targetAppointment }
    req = urllib.request.Request(rescheduleLink)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(data)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    resp = urllib.request.urlopen(req, jsondataasbytes)
    return resp

def getAppointmentID(emailLink):
    arr = emailLink.split("/")
    return arr[len(arr)-1]

def distanceBetween(x1,y1,x2,y2):
    return ((((x2 - x1 )**2) + ((y2-y1)**2) )**0.5)

def searchAppointments():
    emailLink = EMAIL_LINK
    appointmentID = getAppointmentID(emailLink)
    targetX = TARGET_X
    targetY = TARGET_Y
    targetTime = datetime.strptime(TARGET_TIME, '%Y-%m-%dT%H:%M:%S.000Z')
    maxDistance = MAX_DISTANCE 
    availableLocations = []
    selectedAppointment = None

    urlLink = "https://sync-cf2-1.canimmunize.ca/fhir/v1/public/booking-page/17430812-2095-4a35-a523-bb5ce45d60f1/appointment-types"
    with urllib.request.urlopen(urlLink) as url:
        data = json.loads(url.read().decode())
        results = data['results']
        for location in results:
            if location['fullyBooked']==False and "Pfizer" in location['nameEn'] and location['status']== 'active':
                location['distance'] = distanceBetween(targetX,targetY,location['gisX'],location['gisY'])
                if location['distance'] < maxDistance:
                    availableLocations.append(location)

    availableLocations.sort(key=lambda x: x['distance'])

    print(len(availableLocations))

    if len(availableLocations) > 1:
        for location in availableLocations:
            locationUrl = "https://sync-cf2-1.canimmunize.ca/fhir/v1/public/availability/17430812-2095-4a35-a523-bb5ce45d60f1?appointmentTypeId=" + location['id']
            with urllib.request.urlopen(locationUrl) as locationRequest:
                appointmentData = json.loads(locationRequest.read().decode())
                if len(appointmentData) > 0:
                    for availability in appointmentData[0]['availabilities']:
                        appointmentTime = datetime.strptime(availability['time'], '%Y-%m-%dT%H:%M:%S.000Z')
                        if appointmentTime < targetTime:
                            location["datetime"]=availability['time']
                            selectedAppointment = location
                            targetTime = appointmentTime

    return selectedAppointment, appointmentID

stop = False
while stop is False:
    selectedAppointment, appointmentID = searchAppointments()
    if selectedAppointment is not None:
        stop = True
        print(selectedAppointment)
        rescheduleAppointment(appointmentID,selectedAppointment)        
    else:
        print("No Appointment Found")
