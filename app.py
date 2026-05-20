import os
from flask import Flask, render_template, request, jsonify, send_file
from ytmusicapi import YTMusic
import yt_dlp

app = Flask(__name__)
yt = YTMusic()

# İndirilen MP3'lerin geçici olarak tutulacağı klasör
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    # Ana sayfayı (arayüzü) yükler
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_music():
    # Tarayıcıdan gelen arama isteğini işler
    data = request.get_json()
    artist = data.get('artist', '')
    
    if not artist:
        return jsonify([])

    try:
        results = yt.search(artist, filter="songs")
        songs_data = []
        
        for song in results[:20]:
            title = song.get("title", "Bilinmeyen")
            artist_name = song["artists"][0]["name"] if song.get("artists") else "Bilinmeyen"
            video_id = song.get("videoId")
            
            songs_data.append({
                "title": title,
                "artist": artist_name,
                "video_id": video_id
            })
            
        return jsonify(songs_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download_song():
    # İndirme butonuna basıldığında çalışır
    video_id = request.args.get('video_id')
    title = request.args.get('title', 'song')

    if not video_id:
        return "Video ID bulunamadı", 400

    url = f"https://www.youtube.com/watch?v={video_id}"
    # Dosya çakışmalarını önlemek için video_id ismiyle kaydediyoruz
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{video_id}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{file_path}.%(ext)s',
        'cookiesfrombrowser': ('chrome',),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    try:
        # Sunucuya indir ve MP3'e dönüştür
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        final_mp3_path = f"{file_path}.mp3"
        
        # Dosyayı kullanıcının tarayıcısına indirilecek dosya olarak gönder
        return send_file(
            final_mp3_path, 
            as_attachment=True, 
            download_name=f"{title}.mp3"
        )

    except Exception as e:
        return f"İndirme sırasında hata oluştu: {str(e)}", 500

if __name__ == '__main__':
    # Uygulamayı lokalde çalıştır
    app.run(debug=True, port=5000)
