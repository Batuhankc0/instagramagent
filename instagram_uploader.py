from flask import Flask, render_template, request, jsonify
from instagram_uploader import upload_media
import os

app = Flask(__name__)

# Ana sayfayı göstermek için
@app.route('/')
def index():
    return render_template('index.html')

# Yükleme isteğini işlemek için
@app.route('/upload', methods=['POST'])
def handle_upload():
    data = request.get_json()
    media_type = data.get('media_type')
    media_url = data.get('media_url')
    caption = data.get('caption')

    if not media_type or not media_url:
        return jsonify({'status': 'error', 'message': 'Eksik bilgi: Medya türü ve URL zorunludur.'}), 400

    # Instagram'a yükleme işlemini başlat
    result = upload_media(media_type, media_url, caption)

    return jsonify(result)

if __name__ == '__main__':
    # Render gibi platformlarda deploy etmek için port'u dinamik al
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)