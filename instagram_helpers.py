# instagram_helpers.py

import requests
import time
import os

# Bu dosyadaki fonksiyonlar, app.py tarafından çağrılmak üzere burada toplanmıştır.
# Bu, kodun daha düzenli olmasını sağlar.

# GRAPH_API_VERSION'ı doğrudan buradan alabiliriz. Diğer anahtarlar app.py üzerinden gelecek.
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v19.0") # Varsayılan olarak v19.0 kullanır

def create_reels_container(account_id, access_token, video_url, caption):
    """Adım 1: Reels'i yüklemek için bir medya konteyneri oluşturur."""
    print("Adım 1: Medya konteyneri oluşturuluyor...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account_id}/media"
    params = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'share_to_feed': 'true', # Reels'in profil akışında da görünmesini sağlar
        'access_token': access_token
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()  # Bir HTTP hatası oluşursa (4xx veya 5xx) exception fırlatır
        result = response.json()
        if 'id' in result:
            print(f"Başarılı! Konteyner ID'si: {result['id']}")
            return result['id']
        else:
            print(f"Hata: Konteyner oluşturulamadı. Gelen yanıt: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"API isteği sırasında kritik bir hata oluştu: {e}")
        # Hata detaylarını daha iyi görmek için response'u text olarak yazdırabiliriz
        if e.response is not None:
            print(f"Detaylar: {e.response.text}")
        return None

def check_container_status(creation_id, access_token):
    """Oluşturulan konteynerin durumunu periyodik olarak kontrol eder."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{creation_id}"
    params = {'fields': 'status_code', 'access_token': access_token}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        status = response.json().get('status_code')
        print(f"Konteyner durumu: {status}")
        return status
    except requests.exceptions.RequestException as e:
        print(f"Durum kontrolü sırasında hata: {e}")
        return "ERROR"

def publish_reels(account_id, creation_id, access_token):
    """Adım 2: Hazır olan konteyneri yayınlayarak Reels'i görünür hale getirir."""
    print("\nAdım 2: Konteyner yayınlanıyor...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{account_id}/media_publish"
    params = {'creation_id': creation_id, 'access_token': access_token}
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        result = response.json()
        if 'id' in result:
            print(f"🎉 TEBRİKLER! Reels başarıyla yayınlandı! Media ID: {result['id']}")
            return result['id']
        else:
            print(f"Hata: Reels yayınlanamadı. Gelen yanıt: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Yayınlama sırasında kritik bir hata oluştu: {e}")
        if e.response is not None:
            print(f"Detaylar: {e.response.text}")
        return None