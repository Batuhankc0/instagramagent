document.addEventListener('DOMContentLoaded', () => {
    // General Elements
    const statusMessage = document.getElementById('status-message');

    // --- Tab Management ---
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

    // --- Media Uploader Logic ---
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

        showStatus('Process started, please wait... This might take a few minutes.', 'info');
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
            showStatus(`Error: ${result.message}`, 'error');
        }
        uploadButton.disabled = false;
    });

    // --- Comment Management Logic ---
    const fetchPostsButton = document.getElementById('fetch-posts-button');
    const postsSelect = document.getElementById('posts-select');
    const commentsContainer = document.getElementById('comments-container');

    fetchPostsButton.addEventListener('click', async () => {
        showStatus('Fetching latest posts...', 'info');
        const result = await sendRequest('/get-posts', null, 'GET');
        
        if (result.status === 'success' && result.data.length > 0) {
            postsSelect.innerHTML = '<option value="">-- Select a post --</option>'; // Clear and add title
            result.data.forEach(post => {
                const option = document.createElement('option');
                option.value = post.id;
                const captionText = post.caption ? post.caption.replace(/\n/g, ' ').substring(0, 40) + '...' : 'No caption';
                option.textContent = `${post.media_type}: ${captionText}`;
                postsSelect.appendChild(option);
            });
            showStatus('Posts fetched successfully. Please select one.', 'success');
        } else {
            showStatus(result.message || 'No posts found.', 'error');
        }
    });

    postsSelect.addEventListener('change', async () => {
        const mediaId = postsSelect.value;
        if (!mediaId) {
            commentsContainer.innerHTML = '';
            return;
        }
        showStatus('Fetching comments...', 'info');
        const result = await sendRequest('/get-comments', { media_id: mediaId });

        commentsContainer.innerHTML = ''; // Clear previous comments
        if (result.status === 'success' && result.data.length > 0) {
            result.data.forEach(comment => {
                const commentEl = document.createElement('div');
                commentEl.className = 'comment';
                commentEl.innerHTML = `
                    <p class="username">Username: @${comment.username}</p>
                    <p class="comment-text">${comment.text}</p>
                    <form class="reply-form" data-comment-id="${comment.id}">
                        <input type="text" class="reply-input" placeholder="Write a reply..." required>
                        <button type="submit" class="reply-button">Reply</button>
                    </form>
                `;
                commentsContainer.appendChild(commentEl);
            });
            showStatus('Comments fetched successfully.', 'success');
        } else {
            showStatus(result.message || 'No comments found.', 'info');
        }
    });
    
    // Event delegation for reply forms
    commentsContainer.addEventListener('submit', async (event) => {
        if (event.target.classList.contains('reply-form')) {
            event.preventDefault();
            const form = event.target;
            const commentId = form.dataset.commentId;
            const message = form.querySelector('.reply-input').value;
            const button = form.querySelector('.reply-button');

            button.disabled = true;
            showStatus('Sending reply...', 'info');
            
            const result = await sendRequest('/reply', { comment_id: commentId, message: message });

            if (result.status === 'success') {
                showStatus(result.message, 'success');
                form.querySelector('.reply-input').value = ''; // Clear reply box
            } else {
                showStatus(`Error: ${result.message}`, 'error');
            }
            button.disabled = false;
        }
    });

    // --- Helper Functions ---
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
            return { status: 'error', message: `Network error: ${error.message}` };
        }
    }
});