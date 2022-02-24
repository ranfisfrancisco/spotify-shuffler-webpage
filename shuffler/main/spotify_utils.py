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
