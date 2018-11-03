import sys
import praw
import re
import os
import datetime
sys.path.insert(0, '/spotipy/')
import spotipy
from spotipy import oauth2, util
from pprint import pprint
from lib.infos import InfosScript

class Main:

    os.environ['SPOTIPY_CLIENT_ID']='371af5b9ee7146b6b2c038195a54e06a'
    os.environ['SPOTIPY_CLIENT_SECRET']='352f23c6be3148de82b19e7ccc711d61'
    os.environ['SPOTIPY_REDIRECT_URI']='http://localhost:8080'

    #regex 
    #use http://txt2re.com/ to find regex online
    rgExtract = re.compile('(.+(?=))-(.+(?=))')
    rgCleanDate = re.compile('(\[.*\]|\(.*\))') #supprime les années (1999) et [1999]
    rgYoutube = re.compile('^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+')

    username = '118679623'
    spotifyPlaylistName = "r/OldSchoolCoolMusic"
    spotifyPlaylistNameBck = spotifyPlaylistName+"-backup"

    def __init__(self):
        self.main()

        
#############################################################################################
#MAIN
    def main(self):
       self.infos = InfosScript()
       self.mainConnectClient()
       self.mainDeclare()
    #    self.debugPostReddit()
       self.mainProcess()
       self.mainPrint()

    #client
    def mainConnectClient(self):
        self.reddit = self.connectReddit()
        self.spotify = self.connectSpotify()
        self.spotifyUser = self.connectSpotifyUser()

    def mainDeclare(self):
        self.postsAreTracks = list()
        self.postsNotTracks = list()
        self.postsNotRespectRequirements = list()
        self.postsNotHaveScore = list()
        self.tracksAddToPlaylist = list()
        self.tracksAlReadyExist = list()
        self.postWithErros = list()
        self.listPost = list()

    #process
    def mainProcess(self):
        self.infos.infosScriptExec_init()
        self.oscmTracks = self.getPlaylistTracks(self.spotifyPlaylistName)
        self.oscmPlaylist = self.getPlaylist(self.spotifyPlaylistName,True)
        self.oscmPlaylistTracksUri = self.getPlaylistTracksUri(self.spotifyPlaylistName)
        self.backupPlaylist(self.spotifyPlaylistName,self.spotifyPlaylistNameBck)

        # self.listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top(limit=5000))
        # self.listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top("month"))
        self.listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top("week"))
        for post in self.listPost:
            if(self.respectRequirements(post)):
                try:
                    cleanSubTitle = self.cleanDateLink(post.title)
                    artistTrack = self.extractArtistTrackData(cleanSubTitle)
                    uriTrackSpotify = self.searchUriSpotify(self.spotify,artistTrack)
                    if not self.findDouble(uriTrackSpotify,self.oscmPlaylistTracksUri):
                        self.addTrackSpotify(uriTrackSpotify,self.oscmPlaylist)
                except ValueError as er:
                    self.postWithErros.append({"id":post.id,"title":post.title,"error":er})
                    pass

    #print
    def mainPrint(self):
        print("\n")
        self.printPlaylist(self.spotifyPlaylistName)
        print("")
        self.printReport()
        print("")
        self.printErrors()
        print("")
        self.printDoubleTest(self.spotifyPlaylistName)
        print("")
        self.infos.infosScriptExec()       
        print("")


#############################################################################################
#DEBUG
    def debugPostReddit(self):
        # self.listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top(limit=1000))
        # self.listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top("month"))
        self.listPost = list(self.reddit.subreddit('OldSchoolCoolMusic').top("week"))
        for post in self.listPost:
            if(self.respectRequirements(post)):
                try:
                    cleanSubTitle = self.cleanDateLink(post.title)
                    artistTrack = self.extractArtistTrackData(cleanSubTitle)
                    print(post.title)
                    print(cleanSubTitle)
                    print(artistTrack)
                except ValueError as er:
                    self.postWithErros.append({"id":post.id,"title":post.title,"error":er})
                    pass
#             
#############################################################################################
#CONNEXIONS
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
        
        token = util.prompt_for_user_token(self.username, 'playlist-modify-public')
        if token:
            return spotipy.Spotify(auth=token)
#############################################################################################
#POST REQUIREMENTS

    def respectRequirements(self,post):
        if(self.postHaveScoreRequire(post) and self.matchYoutubeLink(post)):
            return True
        else:
            self.postsNotRespectRequirements.append(post)
            return False

    def postHaveScoreRequire(self,post):
        if(post.score > 10):
            return True
        else:
            self.postsNotHaveScore.append(post)
            return False

    def matchYoutubeLink(self,post):
        if not post:
            raise ValueError("link is null or empty")
        
        m = self.rgYoutube.search(post.url)
        if m:
            self.postsAreTracks.append(post)
            return True
        else:
            self.postsNotTracks.append(post)
            return False
#############################################################################################
#SPOTIFY TOOLS
    def getPlaylistTracksUri(self,playlist_name):
        if not playlist_name:
            raise ValueError("playlist params is null or empty")
        
        listTracksUri = list()
        try:
            playlists = self.getPlaylistTracks(playlist_name,"items(track(uri))")
            for item in playlists:
                listTracksUri.append(item['track']['uri'])
            return listTracksUri
        except:
            return list()


    def getPlaylistTracks(self,playlist_name,fields=""):
        if not playlist_name:
            raise ValueError("playlist is null or empty")

        playlist = self.getPlaylist(playlist_name,False)
        totalTrackRemaining = playlist['tracks']['total']
        trackOffset = 0
        playlistTracks = []
        while(totalTrackRemaining > 0):
            limit = 100

            if(totalTrackRemaining < limit):
                limit = totalTrackRemaining
            
            playlistTracks = playlistTracks + self.spotify.user_playlist_tracks(
                    self.username, 
                    playlist['id'],
                    fields=fields,
                    limit=limit,
                    offset=trackOffset)['items']    
            trackOffset += limit
            totalTrackRemaining -= limit
        return playlistTracks

    def getPlaylist(self,playlist_name,create):
        if not playlist_name:
            raise ValueError("playlist is null or empty")

        playlists = self.spotify.user_playlists(self.username)
        for playlist in playlists['items']:
            if(playlist['name'] == playlist_name):
                return playlist
        #if not found, create playlist
        if create:
            self.spotifyUser.user_playlist_create(self.username, playlist_name,True)

    def findDouble(self,uri,playlist):
        if not uri:
            raise ValueError("Uri is null or empty")
        if not playlist:
            raise ValueError("playlist is null or empty")

        if uri in playlist:
            self.tracksAlReadyExist.append(uri)
            return True
        else:
            return False

    def searchUriSpotify(self,spotify,search):
        if not search:
            raise ValueError("@search is null or empty")

        results = self.spotify.search(q=search,type='artist,track',limit=1)
        items = results['tracks']['items']
        if items:
            return(items[0]['uri'])
        raise ValueError(search+"\nURI not found")

    def addTrackSpotify(self,uriTrack,playlist):
        if not uriTrack:
            raise ValueError("URI is null or empty")

        self.tracksAddToPlaylist.append(uriTrack)
        self.spotifyUser.user_playlist_add_tracks(self.username, playlist['id'], [uriTrack])

    def backupPlaylist(self,playlist_name,playlist_name_bck):
        playlistTracksUri = self.getPlaylistTracksUri(playlist_name)
        self.flushPlaylist(playlist_name_bck)
        playlistBackUp = self.spotifyUser.user_playlist_create(self.username, playlist_name_bck,True)

        limit = 99
        if playlistTracksUri:
            while(len(playlistTracksUri) > 0):
                if(len(playlistTracksUri) > limit):
                    tracksToAdd = playlistTracksUri[0:limit]
                    del playlistTracksUri[0:limit]
                else:
                    lastIndex = len(playlistTracksUri)
                    tracksToAdd = playlistTracksUri[0:lastIndex]
                    del playlistTracksUri[0:lastIndex]
                self.spotifyUser.user_playlist_add_tracks(self.username,playlistBackUp['id'],tracksToAdd)
        print("Backup of "+playlist_name+" to "+playlist_name_bck+" done !")
            

    def flushPlaylist(self,playlist_name):
        playlistBackUp = self.getPlaylist(playlist_name,False)
        if playlistBackUp:
            self.spotifyUser.user_playlist_unfollow(self.username,playlistBackUp['id'])

    def searchDoubleInPlaylist(self,playlist_name):
        playlistTrackURI = self.getPlaylistTracks(playlist_name)
        seen = set()
        double = []
        uniq = []
        for item in playlistTrackURI:
            track = item['track']
            uri = item['track']['uri']
            if uri not in seen:
                uniq.append(uri)
                seen.add(uri)
            else:
                double.append(track)
        return double
        
    

#############################################################################################
#REGEX PROCESS

    def cleanDateLink(self,title):
        if not title:
            raise ValueError("title is null or empty ")

        title = self.replaceBadChars(title)
        return self.rgCleanDate.sub("",title)

    def replaceBadChars(self,title):
        title = title.replace("—","-")
        return title

    def extractArtistTrackData(self,title):
        if not title:
            raise ValueError("title is null or empty ")

        iteratorObj = self.rgExtract.finditer(title)
        if( sum(1 for _ in iteratorObj) == 0):
            raise ValueError(title+"\n"+"Impossible d'extraire le titre ou l'artiste")

        for match in self.rgExtract.finditer(title):
            search = match.group(1)+" "+match.group(2)
            return search
#############################################################################################
#OUTPUT FUNCTIONS
    def printReport(self):
        print("#REPORT:")
        print("-----------------------------------------------------------------------")
        print(" %s %s" % ("playlist |",self.oscmPlaylist['name']))
        print(" %s %s" % ("posts find|",len(self.listPost)))
        print(" %s %s" % ("posts = tracks|",len(self.postsAreTracks)))
        print(" %s %s" % ("posts != tracks|",len(self.postsNotTracks)))
        print(" %s %s" % ("posts.score < 10|",len(self.postsNotHaveScore)))
        print(" %s %s" % ("posts no respect requirements|",len(self.postsNotRespectRequirements)))       
        print(" %s %s" % ("tracks added|",len(self.tracksAddToPlaylist)))
        print(" %s %s" % ("tracks already exist|",len(self.tracksAlReadyExist)))
        print(" %s %s" % ("post with errors|",len(self.postWithErros)))

    def printErrors(self):
        print("#ERRORS:")
        print("-----------------------------------------------------------------------")
        for errors in self.postWithErros:
            try:
                print('%s\n' % errors["error"])
            except:
                print('%s\n' % str(errors["error"]).encode())

    def printPlaylist(self,playlist_name): 
        playlistTracks = self.getPlaylistTracks(playlist_name)
        print("#PLAYLIST CONTENT:")
        print("-----------------------------------------------------------------------")
        print("Current playlist tracks (title) (len:"+str(len(playlistTracks))+")")
        for i, item in enumerate(playlistTracks):
            track = item['track']
            try:
                print(" %2.5s %1s - %1s" % (i, track['artists'][0]['name'],track['name']))
            except:
                print(" %2.5s %1s - %1s" % (i, track['artists'][0]['name'].encode(),track['name'].encode()))

    def printDoubleTest(self,playlist_name):
        playlistTracksDouble = self.searchDoubleInPlaylist(playlist_name)
        print("#DOUBLE:")
        print("-----------------------------------------------------------------------")
        for track in playlistTracksDouble:
            print("%0s (%0s) " % (track['name'],track['uri']))
main = Main()