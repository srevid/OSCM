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

    dateTimeNow = datetime.datetime.now()
    addTracks = True
    needBackup = True
    scoreToReach = 10
    terminalErrors = False
    terminalContent = False
    limitSearch = "week" #"week"|"month"|"year"|100

    logFilePath = "./report/logs.txt"
    errorsFilePath = "./report/errors.txt"
    
    userID = '118679623'
    listPlaylistSubredditName = ['ClassicRock','OldSchoolCoolMusic']
        

    def __init__(self):
        self.main()
#############################################################################################
#LOGS
    def writeLogsAndErrors(self):
        with open(self.logFilePath, "a") as logsFile:
            logsFile.write(self.logs)
        with open(self.errorsFilePath, "a") as errorsFile:
            errorsFile.write(self.errors)
    
    def writeEndOfFile(self):
        with open(self.logFilePath, "a") as logsFile:
            logsFile.write("***********************************************************************\n")
            logsFile.write("**** END OF MAIN PROCESS \n")
            logsFile.write("**** DATE:"+self.dateTimeNow.strftime("%m/%d/%Y %H:%M:%S")+"\n")
            logsFile.write("***********************************************************************\n")
        with open(self.errorsFilePath, "a") as errorsFile:
            errorsFile.write("***********************************************************************\n")
            errorsFile.write("**** END OF MAIN PROCESS \n")
            errorsFile.write("**** DATE:"+self.dateTimeNow.strftime("%m/%d/%Y %H:%M:%S")+"\n")
            errorsFile.write("***********************************************************************\n")

    
#############################################################################################
#DEBUG
    def debugPostReddit(self):
        self.listPost = self.getListPost(self.limitSearch)
        for post in self.listPost:
            if(self.respectRequirements(post)):
                try:
                    cleanSubTitle = self.cleanDateLink(post.title)
                    artistTrack = self.extractArtistTrackData(cleanSubTitle)
                    print(post.title +"| raw")
                    print(cleanSubTitle+ "| clean pass")
                    print(artistTrack+ "| artist/track pass")
                except ValueError as er:
                    self.postWithErrors.append({"id":post.id,"title":post.title,"error":er})
                    pass
#        
#############################################################################################
#MAIN
    def main(self):
        self.infos = InfosScript()
        self.mainConnectClient()        
        for playlist in self.listPlaylistSubredditName:
            self.mainDeclare()
            self.playlistSubredditName = playlist
            self.spotifyPlaylistName = "/r/"+self.playlistSubredditName
            self.spotifyPlaylistNameBck = self.spotifyPlaylistName+"-backup"
            self.spotifyPlaylistDescription = "The https://www.reddit.com/r/"+self.playlistSubredditName+" playlist ! The playlist is automatically populated every week from the submissions that reaches a score of "+str(self.scoreToReach)+" or more.**LAST UPDATE: "+self.dateTimeNow.strftime("%m/%d/%Y")+"**"
            self.mainProcess()
            self.mainPrint()
            self.LogAndPrint("---- END OF "+self.playlistSubredditName.upper()+" PROCESS")
            self.writeLogsAndErrors()
        self.writeEndOfFile()

    #client
    def mainConnectClient(self):
        self.reddit = self.connectReddit()
        self.spotify = self.connectSpotify()
        self.spotifyUser = self.connectSpotifyUser()

    #variables
    def mainDeclare(self):
        self.postsAreYoubube = list()
        self.postsAreNotYoubube = list()
        self.postsNotRespectRequirements = list()
        self.postsNotHaveScore = list()
        self.postsTitleMatch = list()
        self.postsTitleNotMatch = list()
        self.tracksCanBeAddToPlaylist = list()
        self.tracksAddedToPlaylist = list()
        self.tracksAlReadyExist = list()
        self.postWithErrors = list()
        self.listPost = list()
        self.logs = ""
        self.errors = ""

    #process
    def mainProcess(self):
        self.infos.infosScriptExec_init()
        self.oscmPlaylist = self.getPlaylist(self.spotifyPlaylistName,True)
        self.oscmTracks = self.getPlaylistTracks(self.spotifyPlaylistName)
        self.oscmPlaylistTracksUri = self.getPlaylistTracksUri(self.spotifyPlaylistName)

        self.updatePlaylistDescription()

        if self.needBackup:
            self.oscmPlaylistBackUp = self.getPlaylist(self.spotifyPlaylistNameBck,True)
            self.backupPlaylist(self.spotifyPlaylistName,self.spotifyPlaylistNameBck)

        self.listPost = self.getListPost(self.limitSearch)
        for post in self.listPost:
            if(self.respectRequirements(post)):
                try:
                    cleanSubTitle = self.cleanDateLink(post.title)
                    artistTrack = self.extractArtistTrackData(cleanSubTitle)
                    uriTrackSpotify = self.searchUriSpotify(self.spotify,artistTrack)
                    if not self.findDouble(uriTrackSpotify,self.oscmPlaylistTracksUri):
                        self.addTrackSpotify(uriTrackSpotify,self.oscmPlaylist)
                except ValueError as er:
                    self.postWithErrors.append({"id":post.id,"title":post.title,"error":er})
                    pass
        self.playlistTracksDouble = self.searchDoubleInPlaylist(self.spotifyPlaylistName)

    #print
    def mainPrint(self):
        self.LogAndPrint("\n")
        self.printPlaylistContent(self.spotifyPlaylistName)
        self.LogAndPrint("")
        self.printReport()
        self.LogAndPrint("")
        self.printErrors()
        self.LogAndPrint("")
        self.printDoubleTest(self.spotifyPlaylistName)
        self.LogAndPrint("")
        self.infos.infosScriptExec()       
        self.LogAndPrint("")

           
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
        
        token = util.prompt_for_user_token(self.userID, 'playlist-modify-public')
        if token:
            return spotipy.Spotify(auth=token)
#############################################################################################
#REDDIT TOOLS
    def getListPost(self,limit):
        if isinstance(limit, str):
            listPost = list(self.reddit.subreddit(self.playlistSubredditName).top(limit))
        else:
            listPost = list(self.reddit.subreddit(self.playlistSubredditName).top(limit=limit))
        return listPost

        
    def respectRequirements(self,post):
        if(self.postHaveScoreRequire(post) and self.matchYoutubeLink(post) and self.matchTitleTrack(post)):
            return True
        else:
            self.postsNotRespectRequirements.append(post)
            return False

    def postHaveScoreRequire(self,post):
        if(post.score > self.scoreToReach):
            return True
        else:
            self.postsNotHaveScore.append(post)
            return False

    def matchYoutubeLink(self,post):
        if not post:
            raise ValueError("link is null or empty")
        
        m = self.rgYoutube.search(post.url)
        if m:
            self.postsAreYoubube.append(post)
            return True
        else:
            self.postsAreNotYoubube.append(post)
            return False

    def matchTitleTrack(self,post):
        if not post:
            raise ValueError("post title is null or empty")

        m = self.rgExtract.search(post.title)
        if m:
            self.postsTitleMatch.append(post)
            return True
        else:
            self.postsTitleNotMatch.append(post)
            return False
#############################################################################################
#SPOTIFY TOOLS
    def updatePlaylistDescription(self):
        self.spotifyUser.user_playlist_change_details(self.userID,self.oscmPlaylist['id'],self.spotifyPlaylistName,None,None,self.spotifyPlaylistDescription)

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
            raise ValueError("getPlaylistTracks:playlist is null or empty")
        
        totalTrackRemaining = self.oscmPlaylist['tracks']['total']
        trackOffset = 0
        playlistTracks = []
        while(totalTrackRemaining > 0):
            limit = 100

            if(totalTrackRemaining < limit):
                limit = totalTrackRemaining
            
            playlistTracks = playlistTracks + self.spotify.user_playlist_tracks(
                    self.userID, 
                    self.oscmPlaylist['id'],
                    fields=fields,
                    limit=limit,
                    offset=trackOffset)['items']    
            trackOffset += limit
            totalTrackRemaining -= limit
        return playlistTracks

    def getPlaylist(self,playlist_name,create):
        if not playlist_name:
            raise ValueError("getPlaylist:playlist is null or empty")

        playlists = self.spotify.user_playlists(self.userID)
        for playlist in playlists['items']:
            if(playlist['name'] == playlist_name):
                return playlist
        #if not found, create playlist
        if create:
            return self.spotifyUser.user_playlist_create(self.userID, playlist_name,True)

    def findDouble(self,uri,playlist):
        if not uri:
            raise ValueError("Uri is null or empty")
        if playlist is None:
            raise ValueError("findDouble:playlist is null or empty")

        if uri in playlist:
            self.tracksAlReadyExist.append(uri)
            return True
        else:
            self.oscmPlaylistTracksUri.append(uri)
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

        self.tracksCanBeAddToPlaylist.append(uriTrack)
        if self.addTracks:
            self.tracksAddedToPlaylist.append(uriTrack)
            self.spotifyUser.user_playlist_add_tracks(self.userID, playlist['id'], [uriTrack])

    def backupPlaylist(self,playlist_name,playlist_name_bck):
        playlistTracksUri = self.getPlaylistTracksUri(playlist_name)
        self.flushPlaylist(playlist_name_bck)
        playlistBackUp = self.spotifyUser.user_playlist_create(self.userID, playlist_name_bck,True)

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
                self.spotifyUser.user_playlist_add_tracks(self.userID,playlistBackUp['id'],tracksToAdd)
        self.LogAndPrint("Backup of "+playlist_name+" to "+playlist_name_bck+" done !")
            

    def flushPlaylist(self,playlist_name):
        if self.oscmPlaylistBackUp:
            self.spotifyUser.user_playlist_unfollow(self.userID,self.oscmPlaylistBackUp['id'])

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
        for match in iteratorObj:
            search = match.group(1)+" "+match.group(2)
            return search
#############################################################################################
#OUTPUT FUNCTIONS
    def printReport(self):
        self.LogAndPrint("#REPORT:")
        self.LogAndPrint("-----------------------------------------------------------------------")
        self.LogAndPrint(" %s %s" % ("playlist |",self.oscmPlaylist['name']))
        self.LogAndPrint(" %s %s" % ("posts find|",len(self.listPost)))
        self.LogAndPrint(" %s %s" % ("posts no respect requirements|",len(self.postsNotRespectRequirements)))       
        self.LogAndPrint(" %s %s" % ("posts.score < 10|",len(self.postsNotHaveScore)))
        self.LogAndPrint(" %s %s" % ("posts = youtube|",len(self.postsAreYoubube)))
        self.LogAndPrint(" %s %s" % ("posts != youbube|",len(self.postsAreNotYoubube)))
        self.LogAndPrint(" %s %s" % ("title = track|",len(self.postsTitleMatch)))
        self.LogAndPrint(" %s %s" % ("title != track|",len(self.postsTitleNotMatch)))
        self.LogAndPrint(" %s %s" % ("tracks can be add|",len(self.tracksCanBeAddToPlaylist)))
        self.LogAndPrint(" %s %s" % ("tracks added|",len(self.tracksAddedToPlaylist)))
        self.LogAndPrint(" %s %s" % ("tracks already exist|",len(self.tracksAlReadyExist)))
        self.LogAndPrint(" %s %s" % ("post with errors|",len(self.postWithErrors)))
        self.LogAndPrint(" %s %s" % ("tracks in double|",len(self.playlistTracksDouble)))

    def printRequirements(self):
        self.LogAndPrint("#REQUIREMENTS:")
        self.LogAndPrint("-----------------------------------------------------------------------")
        self.LogAndPrint("Current post not rearch score of "+str(self.scoreToReach))
        for requireScore in self.postsNotHaveScore:
            try:
                self.LogAndPrint('%s\n' % requireScore.title)
            except:
                self.LogAndPrint('%s\n' % str(requireScore.title).encode())
        self.LogAndPrint("\n")
        self.LogAndPrint("Current post which url not match youtube ")
        for requireTrack in self.postsAreNotYoubube:
            try:
                self.LogAndPrint('%s\n' % requireTrack.title)
            except:
                self.LogAndPrint('%s\n' % str(requireTrack.title).encode())

    def printErrors(self):
        self.ErrorsAndPrint("#ERRORS: "+self.playlistSubredditName)
        self.ErrorsAndPrint("-----------------------------------------------------------------------")
        for errors in self.postWithErrors:
            try:
                self.ErrorsAndPrint('%s\n' % errors["error"])
            except:
                self.ErrorsAndPrint('%s\n' % str(errors["error"]).encode())

    def printPlaylistContent(self,playlist_name): 
        playlistTracks = self.getPlaylistTracks(playlist_name)
        self.LogAndPrint("#PLAYLIST CONTENT: "+self.playlistSubredditName)
        self.LogAndPrint("-----------------------------------------------------------------------")
        self.LogAndPrint("Current playlist tracks (title) (len:"+str(len(playlistTracks))+")")
        for i, item in enumerate(playlistTracks):
            track = item['track']
            try:
                self.LogAndPrint(" %2.5s %1s - %1s" % (i, track['artists'][0]['name'],track['name']))
            except:
                self.LogAndPrint(" %2.5s %1s - %1s" % (i, track['artists'][0]['name'].encode(),track['name'].encode()))

    def printDoubleTest(self,playlist_name):
        
        self.LogAndPrint("#DOUBLE:")
        self.LogAndPrint("-----------------------------------------------------------------------")
        for track in self.playlistTracksDouble:
            self.LogAndPrint("%0s (%0s) " % (track['name'],track['uri']))

    def LogAndPrint(self,message):
        print(message)
        self.logs = self.logs+message+"\n"

    def ErrorsAndPrint(self,message):
        if self.terminalErrors:
            print(message)
        self.errors = self.errors+message+"\n"


main = Main()