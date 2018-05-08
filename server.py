import socket
import os
import tweepy
import datetime
import json

# Consumer keys and access tokens, used for OAuth
consumer_key = 'Your_consumer_key'
consumer_secret = 'Your_consumer_secret'
access_token = 'Your_access_token'
access_token_secret = 'Your_access_token_secret'
 
# OAuth process, using the keys and tokens
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
 
# Creation of the actual interface, using authentication
api = tweepy.API(auth)
 
# Sample method, used to update a status
#api.update_status('Hello World!')

class SocketListener(tweepy.StreamListener):
    ''' Handles data received from the stream. '''
    
    def on_status(self, status):
        # Prints the text of the tweet
        #print type(unicode(datetime.datetime.fromtimestamp(int(status.timestamp_ms) / 1e3)))
        #print type(status.text)
        #print type('\n')
        new_tweet = status.text
        data =  json.dumps({"text": unicode(new_tweet)}, sort_keys=True,indent=4, separators=(',', ':'))
        #data = unicode(new_tweet.encode('UTF-8'))
        # data =  json.dumps({'time': unicode(datetime.datetime.fromtimestamp(int(status.timestamp_ms) / 1e3)).encode("UTF-8"),\
        #                     'text': new_tweet.encode('UTF-8')})
               
        try:
            connection.send(data)
            print "Data sent!"
        except:
            print "Unsuccessful sending"
            raise
        
        #print('Tweet text: ' + status.text)
        # There are many options in the status object,
        # hashtags can be very easily accessed.
        #print status
        #for hashtag in status.entities['hashtags']:
        #    print('Tweet text: ' + hashtag['text'])
        return True
 
    def on_error(self, status_code):
        print('Got an error with status code: ' + str(status_code))
        return True # To continue listening
        
    def on_timeout(self):
        print('Timeout...')
        return True # To continue listening

if __name__ == '__main__':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', 9000))
    server.listen(0)
    while True:
        connection, address = server.accept()
        print("Connection built!")
        listener = SocketListener()
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        stream = tweepy.Stream(auth, listener)
        #stream.filter(locations = [-74,40,-73,41])
        stream.filter(track=['#sports','#china','#policy','#love','#girl','#summer','#smile',\
            '#food','#family','#music','#beach','#cat','#lol','#hot','#flower','#work','#lifestyle',\
            '#instalove','#EXO','#book','#novel','#mustread','#wordcount','#amazon','#twitter','#romantic',\
            '#job','#news','success','#banned','#trade','sports','china','policy','love','girl','summer','smile',\
            'food','family','music','beach','cat','lol','hot','flower','work','lifestyle',\
            'instalove','EXO','book','novel','mustread','wordcount','amazon','twitter','romantic',\
            'job','news','success','banned','trade'])
        
        #connection.send("test: %s"% connection.recv(1024))
    connection.close()
