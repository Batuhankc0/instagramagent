document.addEventListener('DOMContentLoaded', () => {
    // Genel Elementler
    const statusMessage = document.getElementById('status-message');

    // --- Sekme Yönetimi ---
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });

    // --- Medya Yükleme Mantığı ---
    const uploadForm = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const mediaTypeSelect = document.getElementById('media-type');
    const captionContainer = document.getElementById('caption-container');

    mediaTypeSelect.addEventListener('change', () => {
        captionContainer.style.display = mediaTypeSelect.value === 'reel' ? 'block' : 'none';
    });

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const mediaUrl = document.getElementById('media-url').value;
        const caption = document.getElementById('caption').value;

        showStatus('İşlem başlatıldı, lütfen bekleyin... Bu işlem birkaç dakika sürebilir.', 'info');
        uploadButton.disabled = true;

        const result = await sendRequest('/upload', {
            media_type: mediaTypeSelect.value,
            media_url: mediaUrl,
            caption: caption
        });

        if (result.status === 'success') {
            showStatus(result.message, 'success');
            uploadForm.reset();
        } else {
            showStatus(`Hata: ${result.message}`, 'error');
        }
        uploadButton.disabled = false;
    });

    // --- Yorum Yönetimi Mantığı ---
    const fetchPostsButton = document.getElementById('fetch-posts-button');
    const postsSelect = document.getElementById('posts-select');
    const commentsContainer = document.getElementById('comments-container');

    fetchPostsButton.addEventListener('click', async () => {
        showStatus('Son gönderiler getiriliyor...', 'info');
        const result = await sendRequest('/get-posts', null, 'GET');
        
        if (result.status === 'success' && result.data.length > 0) {
            postsSelect.innerHTML = '<option value="">-- Bir gönderi seçin --</option>'; // Temizle ve başlık ekle
            result.data.forEach(post => {
                const option = document.createElement('option');
                option.value = post.id;
                const captionText = post.caption ? post.caption.replace(/\n/g, ' ').substring(0, 40) + '...' : 'Açıklama yok';
                option.textContent = `${post.media_type}: ${captionText}`;
                postsSelect.appendChild(option);
            });
            showStatus('Gönderiler başarıyla getirildi. Lütfen birini seçin.', 'success');
        } else {
            showStatus(result.message || 'Hiç gönderi bulunamadı.', 'error');
        }
    });

    postsSelect.addEventListener('change', async () => {
        const mediaId = postsSelect.value;
        if (!mediaId) {
            commentsContainer.innerHTML = '';
            return;
        }
        showStatus('Yorumlar getiriliyor...', 'info');
        const result = await sendRequest('/get-comments', { media_id: mediaId });

        commentsContainer.innerHTML = ''; // Önceki yorumları temizle
        if (result.status === 'success' && result.data.length > 0) {
            result.data.forEach(comment => {
                const commentEl = document.createElement('div');
                commentEl.className = 'comment';
                // ******************************************************
                // ***** İSTEDİĞİNİZ DEĞİŞİKLİK BU SATIRDA YAPILDI *****
                // ******************************************************
                commentEl.innerHTML = `
                    <p class="username">Kullanıcı Adı: @${comment.username}</p>
                    <p class="comment-text">${comment.text}</p>
                    <form class="reply-form" data-comment-id="${comment.id}">
                        <input type="text" class="reply-input" placeholder="Yanıt yaz..." required>
                        <button type="submit" class="reply-button">Yanıtla</button>
                    </form>
                `;
                commentsContainer.appendChild(commentEl);
            });
            showStatus('Yorumlar başarıyla getirildi.', 'success');
        } else {
            showStatus(result.message || 'Hiç yorum bulunamadı.', 'info');
        }
    });
    
    // Yanıtlama formları için olay delegasyonu
    commentsContainer.addEventListener('submit', async (event) => {
        if (event.target.classList.contains('reply-form')) {
            event.preventDefault();
            const form = event.target;
            const commentId = form.dataset.commentId;
            const message = form.querySelector('.reply-input').value;
            const button = form.querySelector('.reply-button');

            button.disabled = true;
            showStatus('Yanıt gönderiliyor...', 'info');
            
            const result = await sendRequest('/reply', { comment_id: commentId, message: message });

            if (result.status === 'success') {
                showStatus(result.message, 'success');
                form.querySelector('.reply-input').value = ''; // Yanıt kutusunu temizle
            } else {
                showStatus(`Hata: ${result.message}`, 'error');
            }
            button.disabled = false;
        }
    });

    // --- Yardımcı Fonksiyonlar ---
    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = type;
    }

    async function sendRequest(url, body, method = 'POST') {
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (body) {
                options.body = JSON.stringify(body);
            }
            const response = await fetch(url, options);
            return await response.json();
        } catch (error) {
            return { status: 'error', message: `Ağ hatası: ${error.message}` };
        }
    }
});