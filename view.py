import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db
import webapp2
from stream import Stream
from stream import Picture

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from google.appengine.api import images
import jinja2
import os
import json
from math import sin, cos, sqrt, atan2, radians


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class viewStreams(webapp2.RequestHandler):
  def get(self):

    #Change!# streams=Stream.query(Stream.author==users.get_current_user()).order(-Stream.creattime).fetch()
    all_streams=Stream.query().order(-Stream.creattime).fetch()
    user_name = ""

    if users.get_current_user():
        user_name = users.get_current_user().nickname()
        print "yes!"
        print  users.get_current_user().email()

    template_values = {
                'user_name': user_name,
                'all_streams': all_streams,
        }

    template = JINJA_ENVIRONMENT.get_template('view_index.html')
    self.response.write(template.render(template_values))

class viewAllPhotos(webapp2.RequestHandler):
    def get(self):
        all_streams=Stream.query().order(-Stream.creattime).fetch()
        cover_url_list = []
        stream_list = []
        for stream in all_streams:
            stream_list.append(stream.name)
            cover_url_list.append(stream.coverurl)

        dictPassed = {'displayCovers':cover_url_list, 'streamList':stream_list}
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)

class mySubscribe(webapp2.RequestHandler):
    def post(self):
        email = self.request.get("email")
        final_picture = []
        displayImages = []
        caption = []
        streams = Stream.query().fetch()
        #print streams
        #print streams[0]
        #print type(users.get_current_user().nickname())

        #print users.get_current_user()
     #   for stream in streams:

      #      if(users.get_current_user().nickname() in stream.subscribers):
       #         print stream.name
        for stream in streams:
            #print "user0: "+user
           # print type(user)
            print stream.subscribers
            #print type(stream.subscribers[0])
            if(email in stream.subscribers):
              #  print "user1: "+user
                pictures=db.GqlQuery("SELECT *FROM Picture " + "WHERE ANCESTOR IS :1 " +"ORDER BY uploaddate DESC" , db.Key.from_path('Stream',stream.name))
                for pic in pictures:
                    if len(final_picture) < 16:
                      #  print ("user2",pic.uploaddate)
                     #   print("user2",pic.imgkey)
                        final_picture.append(pic)
                        continue
                    else:
                   #     print "user3: "+user
                        if pic.uploaddate > final_picture[15].uploaddate:
                            final_picture.pop()
                            final_picture.append(pic)
                            final_picture.sort(key=lambda pic:pic.uploaddate, reverse=True)

        final_picture.sort(key=lambda pic:pic.uploaddate, reverse=True)
        for f_pic in final_picture:
            #print f_pic.uploaddate
            #f = "http://aptmini3.appspot.com/view_photo/"+f_pic.imgkey
           # f.get_serving_url()
            caption.append(f_pic.caption)
            url = images.get_serving_url(f_pic.imgkey)
            url = url + "=s600"
            displayImages.append(url)
            print url

           # print f_pic.uploaddate


        dictPassed = {'displayImages':displayImages,'caption':caption}
        jsonObj = json.dumps(dictPassed, sort_keys=True,indent=4, separators=(',', ': '))
        self.response.write(jsonObj)




class AndroidViewNearbyPhotos(webapp2.RequestHandler):
    def get(self, photoIndexes, currentLocation):
        passedInCoord = currentLocation.split('_')
        lat = float(passedInCoord[0])
        lon = float(passedInCoord[1])

        displayImageObjs = []
        # displayPhotoList = []

        stream_query = Stream.query()
        for stream in stream_query:
            photos = db.GqlQuery("SELECT * FROM Picture " + "WHERE ANCESTOR IS :1 " +"ORDER BY uploaddate DESC" , db.Key.from_path('Stream', stream.name))
            for photo in photos:
                photoUrl = images.get_serving_url(photo.imgkey)
                photoUrl = str(photoUrl) + "=s500"

                photoDict = {}
                photoDict["photoServingURL"] = photoUrl
                photoDict["date"] = str(photo.uploaddate)
                photoDict["loc"] = str(photo.loc)
                photoDict["streamName"] = str(stream.name)
                # photoDict["streamID"] = str(stream.key.id())
                photoCoord = str(photo.loc).split(',')
                plat = float(photoCoord[0])
                plon = float(photoCoord[1])
                R = 6373.0

                lat1 = radians(lat)
                lon1 = radians(lon)
                lat2 = radians(plat)
                lon2 = radians(plon)

                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = (sin(dlat / 2)) ** 2 + cos(lat1) * cos(lat2) * (sin(dlon / 2)) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance = R * c
                photoDict["actualDistance"] = distance
                if distance > 10:
                    photoDict["strDistance"] = str(distance).split('.', 1)[0] + 'km'
                else:
                    photoDict["strDistance"] = str(distance * 1000).split('.', 1)[0] + 'm'
                displayImageObjs.append(photoDict)

        displayImageObjs = sorted(displayImageObjs, key = lambda k: k['actualDistance'])
        passedPhotos = []
        morePhotos = "False"
        indexURL = photoIndexes
        indexList = str(photoIndexes).split('_')
        if len(displayImageObjs) - 1 > int(indexList[1]):
            for i in range(int(indexList[0]), int(indexList[1]) + 1):
                passedPhotos.append(displayImageObjs[i])
            indexURL = str(int(indexList[0]) + 16) + '_' + str(int(indexList[1]) + 16)
            morePhotos = "True"
        else:
            for i in range(int(indexList[0]), len(displayImageObjs)):
                passedPhotos.append(displayImageObjs[i])

        dictPassed = {'user': None, 'morePhotos': morePhotos, 'indexURL': indexURL,'displayImageObjs': passedPhotos}#'displayPhotoList' : displayStreamList
        jsonObj = json.dumps(dictPassed, sort_keys=True, indent=4, separators=(',', ': '))
        self.response.write(jsonObj)



application = webapp2.WSGIApplication([
    ('/viewallstreams', viewStreams),
    ('/viewAllPhotos',viewAllPhotos),
    ('/mySubscribe',mySubscribe),
    ('/androidViewNearbyPhotos/([^/]+)/([^/]+)', AndroidViewNearbyPhotos)
], debug=True)
