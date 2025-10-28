from flask import Flask, request, render_template, send_from_directory
import os
import time
from dotenv import load_dotenv

# instagram_helpers.py dosyamızdaki fonksiyonları import ediyoruz
from instagram_helpers import create_reels_container, check_container_status, publish_reels

# Ortam değişkenlerini yükle (hem local .env için hem de Render için çalışır)
load_dotenv()

app = Flask(__name__)

# Render'da oluşturduğumuz diskin bağlanacağı yol.
# Bu yolun, Render'daki Disk ayarlarında "Mount Path" ile aynı olması zorunludur.
UPLOAD_FOLDER = '/var/data/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ortam değişkenlerinden hassas bilgileri alıyoruz.
# Bu değişkenler Render'ın "Environment Variables" bölümünde ayarlanmalıdır.
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

# Ana sayfayı (index.html) gösteren route
@app.route('/')
def index():
    return render_template('index.html')

# Yüklenen dosyaları public olarak sunmak için bir route.
# Bu, Instagram'ın videoyu sunucumuzdan çekebilmesi için gereklidir.
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# /upload adresine dosya gönderildiğinde bu fonksiyon çalışır
@app.route('/upload', methods=['POST'])
def upload_file():
    # Başlamadan önce API anahtarlarının varlığını kontrol et
    if not all([ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID]):
        return render_template('result.html', message='Hata: Sunucu tarafında ortam değişkenleri (API Anahtarları) ayarlanmamış.')

    if 'video' not in request.files:
        return render_template('result.html', message='Hata: Formda video dosyası bulunamadı.')
    
    file = request.files['video']
    caption = request.form['caption']
    
    if file.filename == '':
        return render_template('result.html', message='Hata: Geçerli bir dosya seçilmedi.')

    if file:
        # Dosyayı sunucuya kaydetmeden önce geçici bir dosya yolu oluşturalım
        filename = f"{int(time.time())}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # 1. Adım: Videoyu Render'daki diskimize kaydet
            file.save(filepath)
            
            # 2. Adım: Bu dosya için kendi sitemiz üzerinden bir public URL oluştur
            # Render, http'yi https'e otomatik yönlendirir.
            public_video_url = f"{request.host_url}uploads/{filename}"
            print(f"Oluşturulan Public URL: {public_video_url}")

            # 3. Adım: Instagram'a yükleme sürecini başlat
            creation_id = create_reels_container(INSTAGRAM_BUSINESS_ACCOUNT_ID, ACCESS_TOKEN, public_video_url, caption)
            
            if not creation_id:
                raise Exception('Instagram medya konteyneri oluşturulamadı. API yanıtını loglarda kontrol edin.')

            # 4. Adım: Konteynerin durumunu kontrol et ve hazır olana kadar bekle
            max_retries = 20
            for _ in range(max_retries):
                status = check_container_status(creation_id, ACCESS_TOKEN)
                if status == "FINISHED":
                    # 5. Adım: Hazır olan konteyneri yayınla
                    media_id = publish_reels(INSTAGRAM_BUSINESS_ACCOUNT_ID, creation_id, ACCESS_TOKEN)
                    if media_id:
                        return render_template('result.html', message=f'🎉 TEBRİKLER! Reels başarıyla yayınlandı! Media ID: {media_id}')
                    else:
                        raise Exception('Medya konteyneri yayınlanamadı. API yanıtını loglarda kontrol edin.')
                
                elif status == "ERROR":
                    raise Exception('Video işlenirken bir hata oluştu. Lütfen video formatını kontrol edin.')
                
                print("Video Instagram tarafından işleniyor, 15 saniye bekleniyor...")
                time.sleep(15)

            # Eğer döngü biterse, zaman aşımına uğramıştır
            raise Exception('İşlem zaman aşımına uğradı. Instagram videoyu işleyemedi.')

        except Exception as e:
            # Herhangi bir hata durumunda kullanıcıya genel bir hata mesajı göster
            print(f"Bir hata yakalandı: {e}")
            return render_template('result.html', message=f'Hata: {e}')
        
        finally:
            # Her durumda (başarılı veya başarısız) geçici dosyayı sunucudan sil
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Geçici dosya silindi: {filepath}")

# Bu blok, kodu "python app.py" ile local'de çalıştırdığımızda devreye girer.
# Render'da Gunicorn bu kısmı kullanmaz.
if __name__ == '__main__':
    app.run(debug=True)