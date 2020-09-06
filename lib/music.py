import youtube_dl

from threading import Thread
import discord
from discord.voice_client import VoiceClient
from discord.ext import commands
from discord.ext.commands import Bot
from os import remove
from os.path import isfile
from asyncio import sleep
from json import load as loadJson
from spotify import HTTPClient
from random import randint, shuffle
from time import time
from .httpRequests import getJsonResponse

# (In seconds) If a video exceeds this duration, it won't be downloaded.
MAX_VIDEO_DURATION = 900

with open("tokens.json") as tokens:
    tokens = loadJson(tokens)
    api_key = tokens["youtube"]
    spotifyClientId = tokens["spotify"]["clientId"]
    spotifySecretId = tokens["spotify"]["secretId"]

spotifyClient = HTTPClient( spotifyClientId, spotifySecretId)

template =     {
                    "voiceClient": None,
                    "playlist": [
                        
                    ],
                    "search":[

                    ],
                    "loop": 0,
                    "currentSong": None
                }

class video():
    def __init__(self, videoId, title, duration=None):
        self.id = videoId
        self.title = title
        self.duration = duration
        self.startTime = None

    def perCentPlayed(self):
        try:
            return (time() - self.startTime)/self.duration
        
        except ZeroDivisionError:
            return 0
        
        
async def player(context, data):

    serverID = str(context.message.guild.id)
    textChannel = context.message.channel

    data[serverID]["voiceClient"] = await context.message.author.voice.channel.connect()    

    while data[serverID]["voiceClient"].is_connected():

        if not data[serverID]["voiceClient"].is_playing():
            
            await playSong(data, serverID, textChannel)

        await sleep(3)

        # If the bot is alone in the voice channel, the loop ends.
        if len(data[serverID]["voiceClient"].channel.members) == 1:
            await data[serverID]["voiceClient"].disconnect()
            await textChannel.send("Se ha ido todo el mundo, me piro")
           

        # If there are no more songs and the one that was playing is finished, the loop ends.
        elif data[serverID]["currentSong"] == None and not data[serverID]["voiceClient"].is_playing():
            await data[serverID]["voiceClient"].disconnect()
            await textChannel.send("La playlist esta vacia, me piro.")
  
        
    
    try:
        remove("serverAudio/" + serverID + ".mp3")
    except FileNotFoundError:               
        pass
    
    await data[serverID]["voiceClient"].disconnect()
    data[serverID]["voiceClient"] = None
    data[serverID]["loop"] = 0
    data[serverID]["playlist"].clear()
    data[serverID]["currentSong"] = None
    

def downloadSong(videoId, path):
    
    url = "https://www.youtube.com/watch?v={0}".format(videoId)
    
    ydl_opts = {

        'format': 'bestaudio/best',
        'quiet': False,
        'outtmpl': 'musica.mp3',
        'noplaylist': True
    }  
    

    ydl_opts["outtmpl"] = path

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])  # Download into the current working directory
    
async def playSong(data, serverID, textChannel):
    global MAX_VIDEO_DURATION

    # Adds ended song to the end of the playlist if loop == all
    if data[serverID]["loop"] == 2:
        data[serverID]["playlist"].append(data[serverID]["currentSong"])

    # Changes current song info if loop != single
    if data[serverID]["loop"] != 1:
        
        if len(data[serverID]["playlist"]) > 0:
            data[serverID]["currentSong"] = data[serverID]["playlist"][0]
            data[serverID]["playlist"].pop(0)
        else:
            data[serverID]["currentSong"] = None
            return

    # If the song has no id (Most likely becasue it comes from a spotify playlist), here a yt video will be found for that song
    if data[serverID]["currentSong"].id == None:
    
        try:
            vidList = await yt_search(data[serverID]["currentSong"].title)
            data[serverID]["currentSong"].id = vidList["items"][0]["id"]["videoId"]
            
            vidInfo = await getVidInfo(data[serverID]["currentSong"].id)
            data[serverID]["currentSong"].title = vidInfo["title"]
            data[serverID]["currentSong"].duration = vidInfo["duration"]
        
        # If no results are found, this function ends
        except:
            await textChannel.send("Video no disponible.")
            return

    # Gets the duration of the video that will be played, in case it is unknown 
    elif data[serverID]["currentSong"].duration == None:
        info = await getVidInfo(data[serverID]["currentSong"].id)

        if info != None:           
            data[serverID]["currentSong"].duration = info["duration"]
        
        else:
            data[serverID]["currentSong"].duration = 0
    

    # Skips videos that are too long.
    if data[serverID]["currentSong"].duration > MAX_VIDEO_DURATION:
        await textChannel.send("Skipped {0} because it was too long.".format(data[serverID]["currentSong"].title))
        return
        
    # Downloads the song if loop is not on single.
    if data[serverID]["loop"] != 1:
        
        vidID = data[serverID]["currentSong"].id
        try:
                
            try:
                remove("serverAudio/" + serverID + ".mp3")
            except FileNotFoundError:               
                pass

            path = "serverAudio/" + serverID+".mp3"
            p1 = Thread(target=downloadSong, args=(vidID, path))
            p1.start()
                      
            while p1.isAlive():
                await sleep(3)

        except:
            await textChannel.send("Woopsies")

    try:
        data[serverID]["voiceClient"].play(discord.FFmpegPCMAudio("serverAudio/" + serverID + ".mp3"))
        data[serverID]["currentSong"].startTime = time()
    except:
        await textChannel.send("Video no disponible.")

async def yt_search(string):
    global youtube
    
    response = await getJsonResponse(f"https://www.googleapis.com/youtube/v3/search?key={api_key}&part=snippet&type=video&q={string}")

    return response.content

async def sendYtRresults(context, data):

    serverID = context.message.guild.id

    q = context.message.content[6:]

    result = await yt_search(q)

    data[str(serverID)]["search"].clear()     
    embed = discord.Embed(title="Results", colour = discord.Color.green())       
                
    for num, vid in enumerate(result["items"]):
        embed = discord.Embed(title=str(num+1) + ") " + vid["snippet"]["title"], colour = discord.Color.green())  
        embed.set_image(url=vid["snippet"]["thumbnails"]["default"]["url"])
        data[str(serverID)]["search"].append(video(vid["id"]["videoId"], vid["snippet"]["title"]))
        await context.message.channel.send(embed=embed)

async def getVidInfo(idVid):

    info = {
        "title": None,
        "duration": None
    }
     
    try:
        response = await getJsonResponse(f"https://www.googleapis.com/youtube/v3/videos?key={api_key}&part=snippet,contentDetails&id={idVid}")

        if response.status == 200:
            res = response.content
        
        else:
            return None
       
    except:
        return None

    else:
        info["title"] = res["items"][0]["snippet"]["title"]  
        info["duration"] = convertTime(res["items"][0]["contentDetails"]["duration"])

    finally:
        return info
        
    
async def retrievePlaylist(playlistID, order):
    lista = []
    
    try:
        response = await getJsonResponse(f"https://www.googleapis.com/youtube/v3/playlistItems?key={api_key}&part=snippet,contentDetails&maxResults=30&playlistId={playlistID}")
        res = response.content
        
        #res = youtube.playlistItems().list(part="snippet", playlistId=playlistID, maxResults=30).execute()
        title = res["items"][0]["snippet"]["title"]

        for vid in res["items"]:
            title = vid["snippet"]["title"]
            vidID = vid["snippet"]["resourceId"]["videoId"]

            lista.append(video(vidID, title))
    except:
        pass

    if order == "r":
        shuffle(lista)

    return lista



async def spotifyPlaylist(playlistId, order):
    global spotifyClient
    
    playlist = await spotifyClient.get_playlist(playlistId)
    
    lista = []

    if order == "r":
        
        while len(lista) < 30 and len( playlist["tracks"]["items"]) > 0:

            ind = randint(0, len(playlist["tracks"]["items"]) - 1)
            
            title = playlist["tracks"]["items"][ind]["track"]["name"] + " " + playlist["tracks"]["items"][ind]["track"]["artists"][0]["name"]
            vidID = None
            
            lista.append(video(None, title))
            playlist["tracks"]["items"].pop(ind)

    else:
        for song in playlist["tracks"]["items"]:
            
            lista.append(video(None, song["track"]["name"] + " " + song["track"]["artists"][0]["name"]))
            
            if len(lista) >= 30:
                break
        
    return lista

async def spotifyAlbum(albumID, order):

    album = await spotifyClient.album(albumID)
    lista = []

    if order == "r":
        
        while len(lista) < 30 and len( album["tracks"]["items"]) > 0:

            ind = randint(0, len(album["tracks"]["items"]) - 1)
            
            title = album["tracks"]["items"][ind]["name"] + " " + album["tracks"]["items"][ind]["artists"][0]["name"]
            vidID = None
            
            lista.append(video(None, title))
            album["tracks"]["items"].pop(ind)

    else:
        for song in album["tracks"]["items"]:
            
            lista.append(video(None, song["name"] + " " + song["artists"][0]["name"]))
            
            if len(lista) >= 30:
                break
        
    return lista

def convertTime(string):
    n = ""
    H = 0
    M = 0
    S = 0

    for x in string:
       
        if x.isnumeric():
            n += x
        
        elif x == "H":
            H = int(n)
            n = ""

        elif x == "M":
            M = int(n)
            n = ""

        elif x == "S":
            S = int(n)
            n = ""
    
    return H*3600+M*60+S