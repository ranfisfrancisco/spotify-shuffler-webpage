'''Defines what is returned when the endpoints defined in urls.py are accessed.'''

import os
import base64
from django.shortcuts import render, redirect
from django.http import HttpResponse
from dotenv import load_dotenv
import requests
import six
import spotipy
from . import spotify_utils
from . import shuffler

load_dotenv()
# Create your views here.

def index(request):
    '''Returns login HTML page.'''
    return render(request, "main/login.html", {})

def login_request(request):
    '''Redirect to Spotify login page.'''

    scope = 'user-library-read user-read-recently-played playlist-read-private streaming'
    url_scope = "%20".join(scope.split())

    client_id = os.getenv("CLIENT_ID")
    redirect_uri = os.getenv("REDIRECT_URI")
    base_url = "https://accounts.spotify.com/authorize?response_type=code"

    return redirect(
        f'{base_url}&client_id={client_id}&scope={url_scope}&redirect_uri={redirect_uri}')

def callback(request):
    '''Returns user to selection page after login and sets authentication and refresh cookies'''

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

    token_request = requests.post('https://accounts.spotify.com/api/token',
        data = {'code':code, 'redirect_uri': redirect_uri, 'grant_type': 'authorization_code'},
        headers=auth_header)

    if token_request.status_code != 200:
        return redirect('/')

    json = token_request.json()

    access_token = json["access_token"]
    refresh_token = json["refresh_token"]

    response = redirect('/select')
    response.set_cookie('access_token', access_token)
    response.set_cookie('refresh_token', refresh_token)

    return response

def refresh_token_request(request):
    '''Gets a new authentication token and sets the associated cookie to it.'''

    if "refresh_token" not in request.COOKIES:
        return redirect('/')

    refresh_token = request.COOKIES["refresh_token"]
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    auth_header = base64.b64encode(
        six.text_type(client_id + ":" + client_secret).encode("ascii")
    )
    auth_header = {"Authorization": "Basic %s" % auth_header.decode("ascii")}

    refresh_request = requests.post('https://accounts.spotify.com/api/token',
        data = {'grant_type' : 'refresh_token', "refresh_token": refresh_token},
        headers=auth_header)


    if refresh_request.status_code != 200:
        return redirect('/')

    json = refresh_request.json()

    access_token = json["access_token"]

    response = redirect('/select')
    response.set_cookie('access_token', access_token)

    return response


def select(request):
    '''Returns select page with user's playlists loaded.
    Redirects to login page if access_token cookie is not set.'''

    if not "access_token" in request.COOKIES or not "refresh_token" in request.COOKIES:
        return redirect('/login')

    access_token = request.COOKIES["access_token"]

    playlists=[]
    try:
        playlists = spotify_utils.get_playlists(access_token)
    except:
        return redirect('/refresh_token')

    response = render(request, "main/select.html", {"playlists": playlists})
    return response


def queue(request):
    '''Accepts a POST request to the selected number of songs from the selected playlists.
    Does nothing if the access or refresh tokenss are not set.'''

    if not "access_token" in request.COOKIES or not "refresh_token" in request.COOKIES:
        return HttpResponse("ERROR: Tokens not set.")

    # I have no idea why it the HTML page appends [] to the name!
    if "selected_playlists[]" not in request.POST or "queue_limit" not in request.POST:
        return HttpResponse("ERROR: Selected playlists or queue limit not received.")

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
            playlists_tracks.append(tracks)
    except:
        return redirect('/refresh_token')

    recent_tracks = spotify_utils.get_recently_played(access_token)

    shuffled_queue = shuffler.Shuffler.shuffle_multiple_playlists(
        playlists_tracks, recent_tracks, queue_limit=queue_limit,
        no_double_artist=True)

    try:
        spotify_utils.queue_tracks(access_token, shuffled_queue)
        return HttpResponse("Success!")
    except spotipy.exceptions.SpotifyException:
        return HttpResponse("ERROR: Please make sure a device is actively playing.")
