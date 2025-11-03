import requests
import time
import os
from dotenv import load_dotenv

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# --- .env DOSYASINDAN BİLGİLERİ OKU ---
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION")


def check_container_status(creation_id):
    """Oluşturulan konteynerin durumunu periyodik olarak kontrol eder."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{creation_id}"
    params = {'fields': 'status_code', 'access_token': ACCESS_TOKEN}
    print("Konteyner durumu kontrol ediliyor...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        status = response.json().get('status_code')
        print(f"Konteyner durumu: {status}")
        return status
    except requests.exceptions.RequestException as e:
        print(f"Durum kontrolü sırasında hata: {e}")
        return "ERROR"

def publish_container(creation_id):
    """Hazır olan konteyneri yayınlayarak medyayı görünür hale getirir."""
    print("\nKonteyner yayınlanıyor...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
    params = {'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        result = response.json()
        if 'id' in result:
            print(f"Başarıyla yayınlandı! Media ID: {result['id']}")
            return True
        else:
            print(f"Yayınlama hatası: {result}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Yayınlama sırasında kritik hata: {e.response.json()}")
        return False

def process_and_publish_media(creation_id):
    """Oluşturulan bir konteynerin durumunu kontrol eder ve hazır olduğunda yayınlar."""
    if not creation_id:
        return False

    max_retries = 20
    retry_count = 0
    while retry_count < max_retries:
        status = check_container_status(creation_id)
        
        if status == "FINISHED":
            return publish_container(creation_id) # Başarı durumunu döndür
        
        if status == "ERROR":
            print("Medya işlenirken bir hata oluştu.")
            return False # Hata durumunda döngüden çık
        
        print("Medya Instagram tarafından işleniyor, 15 saniye bekleniyor...")
        time.sleep(15)
        retry_count += 1
    
    print("İşlem zaman aşımına uğradı.")
    return False

def upload_media(media_type, media_url, caption=None):
    """
    Gelen isteğe göre Reels veya Hikaye yükleme işlemini başlatır ve tamamlar.
    Bu fonksiyon, app.py tarafından çağrılacak ana fonksiyondur.
    """
    print(f"Yeni yükleme talebi: Tür={media_type}, URL={media_url}")
    api_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    params = {'access_token': ACCESS_TOKEN}

    # Medya türüne göre API parametrelerini ayarla
    if media_type == 'reel':
        params.update({
            'media_type': 'REELS',
            'video_url': media_url,
            'caption': caption or "Python ile yüklendi! 🚀",
            'share_to_feed': 'true'
        })
    elif media_type == 'image_story':
        params.update({
            'media_type': 'STORIES',
            'image_url': media_url
        })
    elif media_type == 'video_story':
        params.update({
            'media_type': 'STORIES',
            'video_url': media_url
        })
    else:
        return {'status': 'error', 'message': 'Geçersiz medya türü.'}

    # Adım 1: Medya Konteynerini Oluştur
    print("Adım 1: Medya konteyneri oluşturuluyor...")
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        result = response.json()

        if 'id' in result:
            creation_id = result['id']
            print(f"Konteyner başarıyla oluşturuldu: {creation_id}. Yayınlama süreci başlatılıyor...")
            
            # Adım 2 & 3: Durumu Kontrol Et ve Yayınla
            success = process_and_publish_media(creation_id)
            if success:
                return {'status': 'success', 'message': 'Medya başarıyla yayınlandı!'}
            else:
                return {'status': 'error', 'message': 'Medya işlenirken veya yayınlanırken bir hata oluştu.'}
        else:
            return {'status': 'error', 'message': f"API Hatası (Konteyner): {result.get('error', {}).get('message', 'Bilinmeyen hata')}"}

    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        print(f"Kritik API Hatası: {error_details}")
        return {'status': 'error', 'message': f"Kritik API Hatası: {error_details}"}