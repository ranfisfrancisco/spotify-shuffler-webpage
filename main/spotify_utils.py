import spotipy

def get_playlists(access_token):
    """Gets a user's playlists.

    Assumes spotipy.spotify object passed in is already authenticated with a user.

    Arguments:

    spotify_conn - spotipy.Spotify object authenticated with user"""
    playlists = []
    offset = 0
    offset_difference = 50

    spotify_conn = spotipy.Spotify(auth=access_token)

    while True:
        results = spotify_conn.current_user_playlists(offset=offset)

        if not results['items']:
            break

        playlists.extend(results['items'])

        if len(results['items']) < offset_difference:
            break

        offset += offset_difference

    return playlists


def get_tracks_from_playlist(access_token, playlist_id):
    """Get tracks from a given playlist

    Assumes spotipy.Spotify object passed in is already authenticated with a user

    Returns list of track dictionary objects from Spotify API.
    Returns empty list if playlist is empty or the playlist was not found.

    Arguments:

    spotify_conn -- spotipy.Spotify object authenticated with a user

    playlist_id -- dictionary object of data from Spotify API for a particular playlist"""

    playlist_tracks = []
    offset = 0
    offset_difference = 100

    spotify_conn = spotipy.Spotify(auth=access_token)

    while True:
        results = spotify_conn.user_playlist_tracks(playlist_id=playlist_id, offset=offset)

        if not results['items']:
            break

        playlist_tracks.extend(results['items'])

        if len(results['items']) < offset_difference:
            break

        offset += offset_difference

    return playlist_tracks

def queue_tracks(access_token, tracks, queue_limit):
    spotify_conn = spotipy.Spotify(auth=access_token)

    for idx, track in enumerate(tracks):
        spotify_conn.add_to_queue(track['track']['uri'])
        if queue_limit is not None and idx + 1 >= queue_limit:
            break

def get_recently_played(access_token):
    spotify_conn = spotipy.Spotify(auth=access_token)
    results = spotify_conn.current_user_recently_played(limit=50)
    recent_track_list = results['items']

    return recent_track_list