from django.shortcuts import render, redirect
from django.http import HttpResponse
from dotenv import load_dotenv
import requests
import os
import six
import base64

# Create your views here.

def index(response):
    return render(response, "main/home.html", {})

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
    
    json = r.json()

    access_token = json["access_token"]
    refresh_token = json["refresh_token"]

    return render(response, "main/select.html", {"access_token" : access_token, "refresh_token" : refresh_token})
