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


# ==============================================================================
# MEDYA YÜKLEME FONKSİYONLARI (MEVCUT KODUNUZ)
# ==============================================================================

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
            return publish_container(creation_id)
        
        if status == "ERROR":
            print("Medya işlenirken bir hata oluştu.")
            return False
        
        print("Medya Instagram tarafından işleniyor, 15 saniye bekleniyor...")
        time.sleep(15)
        retry_count += 1
    
    print("İşlem zaman aşımına uğradı.")
    return False

def upload_media(media_type, media_url, caption=None):
    """Gelen isteğe göre Reels veya Hikaye yükleme işlemini başlatır ve tamamlar."""
    print(f"Yeni yükleme talebi: Tür={media_type}, URL={media_url}")
    api_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    params = {'access_token': ACCESS_TOKEN}

    if media_type == 'reel':
        params.update({'media_type': 'REELS', 'video_url': media_url, 'caption': caption or "Python ile yüklendi! 🚀", 'share_to_feed': 'true'})
    elif media_type == 'image_story':
        params.update({'media_type': 'STORIES', 'image_url': media_url})
    elif media_type == 'video_story':
        params.update({'media_type': 'STORIES', 'video_url': media_url})
    else:
        return {'status': 'error', 'message': 'Geçersiz medya türü.'}

    print("Adım 1: Medya konteyneri oluşturuluyor...")
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        result = response.json()

        if 'id' in result:
            creation_id = result['id']
            print(f"Konteyner başarıyla oluşturuldu: {creation_id}. Yayınlama süreci başlatılıyor...")
            
            success = process_and_publish_media(creation_id)
            if success:
                return {'status': 'success', 'message': 'Medya başarıyla yayınlandı!'}
            else:
                return {'status': 'error', 'message': 'Medya işlenirken veya yayınlanırken bir hata oluştu.'}
        else:
            return {'status': 'error', 'message': f"API Hatası (Konteyner): {result.get('error', {}).get('message', 'Bilinmeyen hata')}"}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"Kritik API Hatası: {error_details}"}


# ==============================================================================
# YENİ EKLENDİ: YORUM YÖNETİMİ FONKSİYONLARI
# ==============================================================================

def get_latest_posts():
    """
    Hesaptaki son 25 gönderiyi ve temel bilgilerini alır.
    app.py'nin hangi gönderinin yorumlarını çekeceğini seçmesi için kullanılır.
    """
    print("Hesaptaki son gönderiler alınıyor...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    params = {
        'fields': 'id,caption,media_type,timestamp,permalink',
        'access_token': ACCESS_TOKEN
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        posts = response.json().get('data', [])
        
        if not posts:
            return {'status': 'success', 'message': 'Hesapta hiç gönderi bulunamadı.', 'data': []}
        
        return {'status': 'success', 'data': posts}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"Gönderiler alınırken hata oluştu: {error_details}"}

def get_comments_for_post(media_id):
    """Belirli bir gönderinin (media_id) yorumlarını alır."""
    print(f"'{media_id}' ID'li gönderi için yorumlar alınıyor...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{media_id}/comments"
    params = {
        'fields': 'id,text,username,timestamp,like_count,from',
        'access_token': ACCESS_TOKEN
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        comments = response.json().get('data', [])

        if not comments:
            return {'status': 'success', 'message': 'Bu gönderide hiç yorum yok.', 'data': []}
            
        return {'status': 'success', 'data': comments}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"Yorumlar alınırken hata oluştu: {error_details}"}

def reply_to_comment(comment_id, message):
    """Belirli bir yoruma (comment_id) yanıt gönderir."""
    print(f"'{comment_id}' ID'li yoruma yanıt gönderiliyor: {message}")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{comment_id}/replies"
    params = {
        'message': message,
        'access_token': ACCESS_TOKEN
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get('id'):
            return {'status': 'success', 'message': 'Yanıt başarıyla gönderildi.'}
        else:
            return {'status': 'error', 'message': f"Yanıt gönderilemedi: {result}"}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"Yanıt gönderilirken hata oluştu: {error_details}"}