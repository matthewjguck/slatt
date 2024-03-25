from flask import Flask, jsonify, render_template, request
import spotipy
import lyricsgenius
import tokens
from spotipy.oauth2 import SpotifyOAuth
import requests



app = Flask(__name__)

# Spotify setup
scope = "user-read-currently-playing"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=tokens.client, 
                                               client_secret=tokens.secret,
                                               redirect_uri="http://127.0.0.1:5100/", 
                                               scope=scope))

# Genius setup
genius = lyricsgenius.Genius(tokens.genius_token)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/lyrics')
def lyrics():
    track_name, artist_names, album_name, album_cover_url = get_current_track_info()
    if track_name:
        song = genius.search_song(track_name, artist_names[0])
        if song:
            # Get the lyrics and remove the first line
            lines = song.lyrics.split('\n')
            if lines:
                lines = lines[1:]  # Remove the first line
            lyrics_without_first_line = '\n'.join(lines)
            
            # Clean the lyrics
            cleaned_lyrics = clean_lyrics(lyrics_without_first_line)
            
            # Return the processed lyrics with the track name, artist, and album cover URL
            return jsonify({'lyrics': cleaned_lyrics, 'track_name': track_name, 'artist': artist_names[0], 'album_cover_url': album_cover_url})
        else:
            return jsonify({'error': 'Lyrics not found.'})
    else:
        return jsonify({'error': 'No track currently playing.'})

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text_to_translate = data.get('q', '')
    source_language = data.get('source', 'auto')
    target_language = data.get('target', 'en')
    format_type = data.get('format', 'text')
    api_key = data.get('api_key', '')

    # Make a POST request to the LibreTranslate API
    response = requests.post("http://127.0.0.1:5500/translate", json={
        'q': text_to_translate,
        'source': source_language,
        'target': target_language,
        'format': format_type,
        'api_key': api_key
    })

    # Check if the request was successful
    if response.status_code == 200:
        translation = response.json()
        return jsonify(translation)
    else:
        return jsonify({'error': 'Translation request failed'}), 500

def get_current_track_info():
    current_track = sp.current_user_playing_track()
    if current_track:
        track_name = current_track['item']['name']
        artist_names = [artist['name'] for artist in current_track['item']['artists']]
        album_name = current_track['item']['album']['name']
        album_cover_url = current_track['item']['album']['images'][0]['url']  # Get the URL of the first image (cover photo)
        return track_name, artist_names, album_name, album_cover_url
    else:
        return None, None, None, None
    
import re

def clean_lyrics(lyrics):
    # Define the pattern to match non-lyrical elements at the end of a line
    pattern = r'\d+Embed$'  # Matches one or more digits followed by 'Embed' at the end of a line
    
    # Remove non-lyrical elements from each line
    cleaned_lyrics = '\n'.join([re.sub(pattern, '', line) for line in lyrics.split('\n')])
    
    return cleaned_lyrics

if __name__ == '__main__':
    app.run(debug=True)
