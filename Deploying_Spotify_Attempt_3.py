from flask import Flask, request, redirect
import requests
import base64
import json
from urllib.parse import urlencode


# Scopes
scopes = [
    'playlist-modify-public',
    'user-read-recently-played',
    'get'
]
scope_string = ' '.join(scopes)

def create_app():

    app = Flask(__name__)
    
    # Your credentials
    client_id = '9e1f5458f3324977a5e672f057cd7182'
    client_secret = '05e24d02bd37494fad84dc96b1f8a665'
    redirect_uri = 'http://3.142.180.207:8000/callback'

    @app.route('/')
    def index():
        print("\nIndex route triggered\n")
        # Authorization endpoint
        auth_url = 'https://accounts.spotify.com/authorize'

        # Parameters
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': scope_string,
        }

        # Create the url
        url = f"{auth_url}?{urlencode(params)}"
        print(f"\n\nAUTH URL SUCCESSFUL\n\n{url}\n")

        # Redirect the user to the Spotify authorization page
        return redirect(url)

    @app.route('/callback')
    def callback():
        print("\n\nCALLBACK\n\n")
        # Get the authorization code from the query parameters
        code = request.args.get('code')

        # Authorization
        authorization = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')

        # Token endpoint
        token_url = 'https://accounts.spotify.com/api/token'

        # Headers
        headers = {
            'Authorization': f'Basic {authorization}'
        }

        # Body
        body = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri
        }

    # Make the post request
        response = requests.post(token_url, headers=headers, data=body)
        print(f"Post Response Status Code: {response.status_code}")
        access_token = response.json().get('access_token')
        refresh_token = response.json().get('refresh_token')

        headers = {
            'Authorization': f"Bearer {access_token}",
        }
        response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        print(f"\nUSER ID ATTEMPT Response Status Code: {response.status_code}")
        user_id = response.json().get('id')
        print(f"\n\nUSER ID: {user_id}\n\n")

        # Playlist endpoint
        playlist_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'


        # Now you can use the access token to make requests on behalf of the user
        # First get recently played tracks
        recently_played_url = 'https://api.spotify.com/v1/me/player/recently-played'
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        params = {
            "limit": 50
        }
        response = requests.get(recently_played_url, headers=headers, params=params)
        print(f"\nRecently Played Response Status Code: {response.status_code}")
        recently_played = response.json().get('items')
        #print(f"Recent: {recently_played}")

        # Get the artists from the recently played tracks
        if recently_played == None:
            print("something went quite wrong")
            return "Oopsie Daisy"
        artist_ids = list(set([track.get('track').get('artists')[0].get('id') for track in recently_played]))
        
        track_uris = []

        for artist_id in artist_ids:
            top_tracks_url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US'
            response = requests.get(top_tracks_url, headers=headers)
            top_tracks = response.json().get('tracks')
            top_track_uri = top_tracks[0].get('uri')
            track_uris.append(top_track_uri)
            top_track_uri = top_tracks[1].get('uri')
            track_uris.append(top_track_uri)
        #print(f"top_tracks: {top_tracks}")

       # playlist_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        create_playlist_url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
        body = {
                'name': 'Recently Played Artists Top Tracks',
                'description': 'A playlist containing the top track from each artist I have recently listened to.',
                'public': True
            }
        response = requests.post(create_playlist_url, headers=headers, json=body)
        print(f"\nPlaylist Response Status Code: {response.status_code}")
      #  print(f"\n\n{response.json()}\n\n")
        playlist_id = response.json().get('id')
      #  print(f"ID: {playlist_id}")
        # Add the top tracks to the playlist
        add_tracks_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        body = {
        'uris': track_uris,
        }   

        response = requests.post(add_tracks_url,headers=headers,json=body)
        print(f"\n Add tracks Response Status Code: {response.status_code}")
        # should get a 201 response code if the playlist was created successfully
        print(response.status_code)
        return "Worked"
    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug=True)