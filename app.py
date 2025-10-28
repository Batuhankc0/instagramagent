# app.py

from flask import Flask, request, render_template, send_from_directory
import os
import time
from dotenv import load_dotenv

# Diğer dosyamızdaki fonksiyonları import ediyoruz
from instagram_helpers import create_reels_container, check_container_status, publish_reels

# Render'ın ortam değişkenlerini yüklemesi için load_dotenv() yine de faydalı olabilir
load_dotenv()

app = Flask(__name__)

# Render'da oluşturacağımız Diskin bağlanacağı yol. Bu standart bir yoldur.
UPLOAD_FOLDER = '/var/data/uploads'
# Bu klasörün var olduğundan emin olalım (Render diski otomatik oluşturur ama local test için iyidir)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ortam değişkenlerini alalım
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

# Ana sayfayı (index.html) göster
@app.route('/')
def index():
    return render_template('index.html')

# Yüklenen dosyaları public olarak sunmak için bir yol (route)
# Bu, Instagram'ın videoyu çekebilmesi için gereklidir
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# /upload adresine dosya gönderildiğinde bu fonksiyon çalışır
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return render_template('result.html', message='Hata: Formda video dosyası bulunamadı.')
    
    file = request.files['video']
    caption = request.form['caption']
    
    if file.filename == '':
        return render_template('result.html', message='Hata: Geçerli bir dosya seçilmedi.')

    if file:
        # 1. Dosyayı Render'daki diskimize güvenli bir isimle kaydet
        filename = f"{int(time.time())}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 2. Bu dosya için kendi sitemiz üzerinden bir public URL oluştur
        # request.host_url, "https://reels-agent.onrender.com/" gibi bir adres verir
        public_video_url = f"{request.host_url}uploads/{filename}"
        print(f"Oluşturulan Public URL: {public_video_url}")

        # 3. Instagram'a yükleme sürecini başlat
        creation_id = create_reels_container(INSTAGRAM_BUSINESS_ACCOUNT_ID, ACCESS_TOKEN, public_video_url, caption)
        
        if not creation_id:
            os.remove(filepath) # Hata olursa geçici dosyayı sil
            return render_template('result.html', message='Hata: Instagram medya konteyneri oluşturulamadı.')

        # 4. Konteyner hazır olana kadar bekle
        max_retries = 20
        for _ in range(max_retries):
            status = check_container_status(creation_id, ACCESS_TOKEN)
            if status == "FINISHED":
                # 5. Yayınla!
                media_id = publish_reels(INSTAGRAM_BUSINESS_ACCOUNT_ID, creation_id, ACCESS_TOKEN)
                os.remove(filepath) # Başarıdan sonra geçici dosyayı sil
                if media_id:
                    return render_template('result.html', message=f'🎉 TEBRİKLER! Reels başarıyla yayınlandı! Media ID: {media_id}')
                else:
                    return render_template('result.html', message='Hata: Medya konteyneri yayınlanamadı.')
            
            elif status == "ERROR":
                os.remove(filepath) # Hata olursa geçici dosyayı sil
                return render_template('result.html', message='Hata: Video işlenirken bir hata oluştu. Lütfen video formatını kontrol edin.')
            
            time.sleep(15)

        os.remove(filepath) # Zaman aşımından sonra geçici dosyayı sil
        return render_template('result.html', message='Hata: İşlem zaman aşımına uğradı. Instagram videoyu işleyemedi.')

if __name__ == '__main__':
    # Bu kısım Render'da Gunicorn tarafından yönetilecek, ama local test için gerekli
    app.run(debug=True)