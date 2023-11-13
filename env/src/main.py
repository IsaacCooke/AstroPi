from picamera import PiCamera
from datetime import datetime, timedelta
from orbit import satellite

def capture(camera, image):
    iss = satellite(25544)
    iss_lat = iss.lat()
    iss_long = iss.long()

    south, exif_lat = convert(iss_lat)
    west, exif_long = convert(iss_long)

    camera.exif_tags['GPS.GPSLatitude'] = exif_lat
    camera.exif_tags['GPS.GPSLatitudeRed'] = 's' if south else 'n'
    camera.exif_tags['GPS.GPSLongitude'] = exif_long
    camera.exif_tags['GPS.GPSLongitude'] = 'w' if west else 'e'

    camera.capture(image)

