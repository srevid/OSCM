import praw
import re
import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util
from lib.infos import InfosScript

class Main:

    #client
    reddit = connectReddit()
    spotify = connectSpotify()
    spotifyUser = connectSpotifyUser()

    #infos
    infos = InfosScript()

    #regex 
    rgExtract = re.compile('(.+(?=)) - (.+(?=))')
    rgCleanDate = re.compile('(\\(.*\\))')
    rgYoutube = re.compile('^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+')

    def start(self):
        self.infos.infosScriptExec_init()
        listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top('week'))
        for submission in listPost:
            

    def postHaveScoreRequire(post):
        if(post.score > 10):
            return true
        else
            return false

    def connectReddit(self):
        reddit_client_id = "mKrZFZXOr3zi7w"
        reddit_client_secret = "cXDR5UMAo2hf8VZObYfgjPrH-TE"
        reddit_user_agent = "desktop:ca.jrans.oscm:v1 (by /u/srevid)"
        client = praw.Reddit(client_id=reddit_client_id,
                            client_secret=reddit_client_secret,
                            user_agent=reddit_user_agent)
        return client

    def connectSpotify(self):
        spot_client_id = "371af5b9ee7146b6b2c038195a54e06a"
        spot_client_key = "352f23c6be3148de82b19e7ccc711d61"
        credentials = oauth2.SpotifyClientCredentials(client_id=spot_client_id,client_secret=spot_client_key)
        token = credentials.get_access_token()
        return spotipy.Spotify(auth=token)

    def connectSpotifyUser(self):
        username = '118679623'
        token = util.prompt_for_user_token(username, 'playlist-modify-public')
        if token:
            return spotipy.Spotify(auth=token)

    def matchYoutubeLink(self,rg,link):
        #use http://txt2re.com/ to find regex online
        m = rg.search(link)
        if m:
            return True
        else:
            return False

    def searchUriSpotify(self,spotify,search):
        results = spotify.search(q=search,type='artist,track',limit=1)
        items = results['tracks']['items']
        if(len(items) > 0):
            if(id not in items[0]):
                return(items[0]['uri'])

    def addTrackSpotify(self,spotipy,uriTrack):
        spotipy.user_playlist_add_tracks('118679623', '4ehKkbzdRgtjn0YK2c7on2', [uriTrack])

    def cleanDateLink(self,rg,title):
        return rg.sub("",title)

    def extractArtistTrackData(self,rg,title):
        for match in rg.finditer(title):
            return(match.group(1)+" "+match.group(2))



main = Main()
main.start()