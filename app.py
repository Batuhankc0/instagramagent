from flask import Flask, render_template, request, jsonify
# YENİ EKLENEN FONKSİYONLARI İÇERİ ALIYORUZ
from instagram_uploader import upload_media, get_latest_posts, get_comments_for_post, reply_to_comment
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# --- MEDYA YÜKLEME ---
@app.route('/upload', methods=['POST'])
def handle_upload():
    data = request.get_json()
    media_type = data.get('media_type')
    media_url = data.get('media_url')
    caption = data.get('caption')

    if not media_type or not media_url:
        return jsonify({'status': 'error', 'message': 'Eksik bilgi: Medya türü ve URL zorunludur.'}), 400
    
    result = upload_media(media_type, media_url, caption)
    return jsonify(result)

# --- YENİ EKLENDİ: YORUM YÖNETİMİ YOLLARI ---

@app.route('/get-posts', methods=['GET'])
def handle_get_posts():
    """Hesaptaki son gönderileri getiren yol."""
    result = get_latest_posts()
    return jsonify(result)

@app.route('/get-comments', methods=['POST'])
def handle_get_comments():
    """Belirli bir gönderinin yorumlarını getiren yol."""
    data = request.get_json()
    media_id = data.get('media_id')
    if not media_id:
        return jsonify({'status': 'error', 'message': 'Geçerli bir Media ID gerekli.'}), 400
    
    result = get_comments_for_post(media_id)
    return jsonify(result)

@app.route('/reply', methods=['POST'])
def handle_reply():
    """Belirli bir yoruma yanıt veren yol."""
    data = request.get_json()
    comment_id = data.get('comment_id')
    message = data.get('message')
    if not comment_id or not message:
        return jsonify({'status': 'error', 'message': 'Yorum ID\'si ve mesaj gerekli.'}), 400
        
    result = reply_to_comment(comment_id, message)
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)