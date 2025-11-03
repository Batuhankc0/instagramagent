document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const button = document.getElementById('upload-button');
    const statusMessage = document.getElementById('status-message');
    const mediaTypeSelect = document.getElementById('media-type');
    const captionContainer = document.getElementById('caption-container');

    // Sadece Reels için açıklama alanını göster
    mediaTypeSelect.addEventListener('change', () => {
        if (mediaTypeSelect.value === 'reel') {
            captionContainer.style.display = 'block';
        } else {
            captionContainer.style.display = 'none';
        }
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Sayfanın yeniden yüklenmesini engelle

        const mediaType = mediaTypeSelect.value;
        const mediaUrl = document.getElementById('media-url').value;
        const caption = document.getElementById('caption').value;

        button.disabled = true;
        button.textContent = 'Yükleniyor...';
        statusMessage.textContent = 'İşlem başlatıldı, lütfen bekleyin... Bu işlem birkaç dakika sürebilir.';
        statusMessage.className = 'info';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    media_type: mediaType,
                    media_url: mediaUrl,
                    caption: caption
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                statusMessage.textContent = result.message;
                statusMessage.className = 'success';
                form.reset(); // Formu temizle
            } else {
                statusMessage.textContent = `Hata: ${result.message}`;
                statusMessage.className = 'error';
            }
        } catch (error) {
            statusMessage.textContent = `Bir ağ hatası oluştu: ${error}`;
            statusMessage.className = 'error';
        } finally {
            button.disabled = false;
            button.textContent = 'Yükle';
        }
    });
});