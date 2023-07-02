import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import re

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


class MemoryCache:
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


def api(youtubeId):
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

    # Get credentials and create an API client

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey="AIzaSyAgzm-RyjajDuNfnuc1DzbqynK1ptUVybk", cache=MemoryCache())

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=youtubeId
    )
    response = request.execute()

    dat = response["items"]
    # vat = dat["snippet"]
    return response['items'][0]['snippet']['description']


def start_project():
    youtubeLink: str = input("provide youtube link")
    YoutubeDesc = getYouTubeDescription(youtubeLink)
    extractedSongs = ExtractSongsFromYoutubeDesc(YoutubeDesc)
    Spotify_Api(extractedSongs)


def ExtractSongsFromYoutubeDesc(YoutubeDesc):
    pattern = '(\d{1,2}(?:\:\d{1,2}){1,2})(?:(\))|\])*(.)([^\n]+)'
    x = re.findall(pattern, YoutubeDesc)
    # returns a dict {Song : Artist}
    return {x[i][-1].split('-')[1].strip() : x[i][-1].split('-')[0].strip().lower()  for i in range(len(x))}


def getYouTubeDescription(youtubeLink):
    youtubeId = getYoutubeIdFromLink(youtubeLink)
    return api(youtubeId)


def getYoutubeIdFromLink(youtubeLink):
    video_id = youtubeLink.split('v=')[1]
    ampersandPosition = video_id.index('&') if '&' in video_id else None
    if ampersandPosition != -1:
        video_id = video_id[0:ampersandPosition]

    return video_id


def Spotify_Api(extractedSongs):
    SPOTIFY_CLIENT_ID = ""
    SPOTIFY_CLIENT_SECRET = ""
    SPOTIFY_REDIRECT_URI = ""

    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    import json

    scope = "playlist-modify-public"
    username = ""

    token = SpotifyOAuth(scope=scope, username=username, client_id=SPOTIFY_CLIENT_ID,
                         client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIFY_REDIRECT_URI)
    spotifyObject = spotipy.Spotify(auth_manager=token)

    playlist_name = input("ENter Playlist name ")
    playlist_description = input("Enter Description ")
    spotifyObject.user_playlist_create(user=username, name=playlist_name, public=True, description=playlist_description)

    # Add songs
    listOfSongs = []
    listOfSongs = SpotifySearch(spotifyObject, extractedSongs)

    prePlaylist = spotifyObject.user_playlists(user=username)
    playlist = prePlaylist['items'][0]['id']

    spotifyObject.playlist_add_items(playlist_id=playlist, items=listOfSongs)


def SpotifySearch(spotifyObject, extractedSongs: dict):
    listOfSongs = []

    for i in extractedSongs:
        print(i)
        result = spotifyObject.search(q=i, limit=50)
        track_items = result['tracks']['items']
        artist_songId_dict = {}
        for j in range(len(track_items)):
            current_artist_name = result['tracks']['items'][j]['artists'][0]['name']
            track_uri = result['tracks']['items'][j]['uri']
            artist_songId_dict[current_artist_name.lower()] = track_uri
        if extractedSongs[i] in artist_songId_dict:
            listOfSongs.append(artist_songId_dict[extractedSongs[i]])
    return listOfSongs

if __name__ == '__main__':
    start_project()
