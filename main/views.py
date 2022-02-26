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

# Create your views here.

def index(response):
    return render(response, "main/login.html", {})

def login(response):
    load_dotenv()
    scope = 'user-library-read user-read-recently-played playlist-read-private streaming'
    url_scope = "%20".join(scope.split())

    return redirect(f'https://accounts.spotify.com/authorize?response_type=code&client_id={os.getenv("CLIENT_ID")}&scope={url_scope}&redirect_uri={os.getenv("REDIRECT_URI")}')

def callback(response):
    if not "code" in response.GET:
        return index(response)

    load_dotenv()

    code = response.GET["code"]
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    redirect_uri = os.getenv("REDIRECT_URI")

    auth_header = base64.b64encode(
        six.text_type(client_id + ":" + client_secret).encode("ascii")
    )
    auth_header = {"Authorization": "Basic %s" % auth_header.decode("ascii")}

    r = requests.post('https://accounts.spotify.com/api/token', data = {'code':code, 'redirect_uri': redirect_uri, 'grant_type': 'authorization_code'},
        headers=auth_header)

    if r.status_code != 200:
        return redirect('/')
    
    json = r.json()

    access_token = json["access_token"]
    refresh_token = json["refresh_token"]

    return redirect(f'/select?access_token={access_token}&refresh_token={refresh_token}')

def refresh_token_request(response):
    refresh_token = response.GET["refresh_token"]
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    auth_header = base64.b64encode(
        six.text_type(client_id + ":" + client_secret).encode("ascii")
    )
    auth_header = {"Authorization": "Basic %s" % auth_header.decode("ascii")}
        
    r = requests.post('https://accounts.spotify.com/api/token', data = {'grant_type' : 'refresh_token', "refresh_token": refresh_token},
        headers=auth_header)

    if r.status_code != 200:
        return redirect('/')

    json = r.json()

    access_token = json["access_token"]

    return redirect(f'/select?access_token={access_token}&refresh_token={refresh_token}')


def select(response):
    if not "access_token" in response.GET or not "refresh_token" in response.GET:
        return redirect('login')

    access_token = response.GET["access_token"]
    refresh_token = response.GET["refresh_token"]
    server_msg = ""

    if "selected_playlists" in response.POST and "queue_limit" in response.POST:
        selected_playlists = response.POST.getlist("selected_playlists")
        queue_limit = response.POST["queue_limit"]

        # TODO: HANDLE
        queue_limit = int(queue_limit)
        if queue_limit == 0:
            queue_limit = float("inf")

        tracks = []

        for playlist_id in selected_playlists:
            tracks.extend(spotify_utils.get_tracks_from_playlist(access_token, playlist_id))

        # Remove Duplicate Tracks based on URI
        tracks = list({ track_data['track']['uri'] : track_data for track_data in tracks }.values())

        recent_tracks = spotify_utils.get_recently_played(access_token)

        shuffled_queue = shuffler.Shuffler.shuffle(tracks, recent_tracks)

        try:
            spotify_utils.queue_tracks(access_token, shuffled_queue, queue_limit)
            server_msg = "Success!"
        except spotipy.exceptions.SpotifyException:
            server_msg = "ERROR: Please make sure a device is actively playing."
    
    playlists = spotify_utils.get_playlists(access_token)
    return render(response, "main/select.html", {"access_token" : access_token, "refresh_token" : refresh_token, "playlists": playlists, "server_msg": server_msg})