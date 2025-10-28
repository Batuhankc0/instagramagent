# app.py - Son Düzeltme Sürümü

from flask import Flask, request, render_template, send_from_directory
import os
import time
from dotenv import load_dotenv

from instagram_helpers import create_reels_container, check_container_status, publish_reels

load_dotenv()

app = Flask(__name__)

UPLOAD_FOLDER = '/var/data/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not all([ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID]):
        return render_template('result.html', message='Hata: Sunucu ortam değişkenleri (API Anahtarları) ayarlanmamış.')

    if 'video' not in request.files:
        return render_template('result.html', message='Hata: Formda video dosyası bulunamadı.')
    
    file = request.files['video']
    caption = request.form['caption']
    
    if file.filename == '':
        return render_template('result.html', message='Hata: Geçerli bir dosya seçilmedi.')

    filepath = None  # filepath'i başlangıçta None olarak ayarlıyoruz
    try:
        if file:
            filename = f"{int(time.time())}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            print(f"Dosya şuraya kaydedilmeye çalışılıyor: {filepath}")
            file.save(filepath)

            # KAYDETME İŞLEMİNİ KONTROL ET
            if not os.path.exists(filepath):
                raise Exception(f"Kritik Hata: Dosya diske kaydedilemedi! Yol: {filepath}")
            
            print("Dosya diske başarıyla kaydedildi.")

            public_video_url = f"{request.host_url}uploads/{filename}"
            print(f"Oluşturulan Public URL: {public_video_url}")

            creation_id = create_reels_container(INSTAGRAM_BUSINESS_ACCOUNT_ID, ACCESS_TOKEN, public_video_url, caption)
            
            if not creation_id:
                raise Exception('Instagram medya konteyneri oluşturulamadı.')

            max_retries = 20
            for _ in range(max_retries):
                status = check_container_status(creation_id, ACCESS_TOKEN)
                if status == "FINISHED":
                    media_id = publish_reels(INSTAGRAM_BUSINESS_ACCOUNT_ID, creation_id, ACCESS_TOKEN)
                    if media_id:
                        return render_template('result.html', message=f'🎉 TEBRİKLER! Reels başarıyla yayınlandı! Media ID: {media_id}')
                    else:
                        raise Exception('Medya konteyneri yayınlanamadı.')
                
                elif status == "ERROR":
                    raise Exception('Video işlenirken bir hata oluştu. Lütfen video formatını kontrol edin.')
                
                print("Video Instagram tarafından işleniyor, 15 saniye bekleniyor...")
                time.sleep(15)

            raise Exception('İşlem zaman aşımına uğradı.')

    except Exception as e:
        print(f"Bir hata yakalandı: {e}")
        return render_template('result.html', message=f'Hata: {e}')
    
    finally:
        # Sadece filepath tanımlıysa ve dosya varsa silmeye çalış
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            print(f"Geçici dosya silindi: {filepath}")

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.run(debug=True)