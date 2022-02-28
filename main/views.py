import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from dotenv import load_dotenv
import requests
import os
import six
import base64
import spotipy
from . import spotify_utils
from . import shuffler

load_dotenv()
# Create your views here.

def index(request):
    return render(request, "main/login.html", {})

def login_request(request):
    scope = 'user-library-read user-read-recently-played playlist-read-private streaming'
    url_scope = "%20".join(scope.split())

    return redirect(f'https://accounts.spotify.com/authorize?response_type=code&client_id={os.getenv("CLIENT_ID")}&scope={url_scope}&redirect_uri={os.getenv("REDIRECT_URI")}')

def callback(request):
    if not "code" in request.GET:
        return redirect('/')

    code = request.GET["code"]
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    redirect_uri = os.getenv("REDIRECT_URI")

    auth_header = base64.b64encode(
        six.text_type(client_id + ":" + client_secret).encode("ascii")
    )
    auth_header = {"Authorization": "Basic %s" % auth_header.decode("ascii")}

    token_request = requests.post('https://accounts.spotify.com/api/token', data = {'code':code, 'redirect_uri': redirect_uri, 'grant_type': 'authorization_code'},
        headers=auth_header)

    if token_request.status_code != 200:
        return redirect('/')
    
    json = token_request.json()

    access_token = json["access_token"]
    refresh_token = json["refresh_token"]

    response = redirect(f'/select')
    response.set_cookie('access_token', access_token)
    response.set_cookie('refresh_token', refresh_token)

    return response

def refresh_token_request(request):
    if "refresh_token" not in request.COOKIES:
        return redirect('/')

    refresh_token = request.COOKIES["refresh_token"]
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    auth_header = base64.b64encode(
        six.text_type(client_id + ":" + client_secret).encode("ascii")
    )
    auth_header = {"Authorization": "Basic %s" % auth_header.decode("ascii")}
    
    refresh_request = requests.post('https://accounts.spotify.com/api/token', data = {'grant_type' : 'refresh_token', "refresh_token": refresh_token},
        headers=auth_header)


    if refresh_request.status_code != 200:
        return redirect('/')

    json = refresh_request.json()

    access_token = json["access_token"]

    response = redirect('/select')
    response.set_cookie('access_token', access_token)

    return response


def select(request):
    if not "access_token" in request.COOKIES or not "refresh_token" in request.COOKIES:
        return redirect('/login')

    access_token = request.COOKIES["access_token"]
    refresh_token = request.COOKIES["refresh_token"]
    
    playlists=[]
    try:
        playlists = spotify_utils.get_playlists(access_token)
    except:
        return redirect('/refresh_token')

    response = render(request, "main/select.html", {"playlists": playlists})
    return response


def queue(request):
    if not "access_token" in request.COOKIES or not "refresh_token" in request.COOKIES:
        return

    # I have no idea why it the HTML page appends [] to the name!
    if "selected_playlists[]" not in request.POST or "queue_limit" not in request.POST:
        return 

    access_token = request.COOKIES["access_token"]
    default_queue_limit = 20
    selected_playlists = request.POST.getlist("selected_playlists[]")
    queue_limit = request.POST["queue_limit"]

    if queue_limit.isnumeric():
        queue_limit = int(queue_limit)
    else:
        queue_limit = default_queue_limit

    playlists_tracks = []

    try:
        for playlist_id in selected_playlists:
            tracks = spotify_utils.get_tracks_from_playlist(access_token, playlist_id)
            # Remove Duplicate Tracks based on URI
            # tracks = list({ track_data['track']['uri'] : track_data for track_data in tracks }.values())
            playlists_tracks.append(tracks)
    except:
        return redirect('/refresh_token')

    recent_tracks = spotify_utils.get_recently_played(access_token)

    shuffled_queue = shuffler.Shuffler.shuffle_multiple_playlists(playlists_tracks, recent_tracks, queue_limit=queue_limit,
    no_double_artist=True)

    try:
        spotify_utils.queue_tracks(access_token, shuffled_queue)
        return HttpResponse("Success!")
    except spotipy.exceptions.SpotifyException:
        return HttpResponse("ERROR: Please make sure a device is actively playing.")