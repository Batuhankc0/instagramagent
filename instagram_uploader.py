import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION")


# ==============================================================================
# MEDIA UPLOAD FUNCTIONS
# ==============================================================================

def check_container_status(creation_id):
    """Periodically checks the status of the created container."""
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{creation_id}"
    params = {'fields': 'status_code', 'access_token': ACCESS_TOKEN}
    print("Checking container status...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        status = response.json().get('status_code')
        print(f"Container status: {status}")
        return status
    except requests.exceptions.RequestException as e:
        print(f"Error during status check: {e}")
        return "ERROR"

def publish_container(creation_id):
    """Publishes the ready container to make the media visible."""
    print("\nPublishing container...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish"
    params = {'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        result = response.json()
        if 'id' in result:
            print(f"Successfully published! Media ID: {result['id']}")
            return True
        else:
            print(f"Publishing error: {result}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Critical error during publishing: {e.response.json()}")
        return False

def process_and_publish_media(creation_id):
    """Checks the status of a created container and publishes it when ready."""
    if not creation_id:
        return False

    max_retries = 20
    retry_count = 0
    while retry_count < max_retries:
        status = check_container_status(creation_id)
        
        if status == "FINISHED":
            return publish_container(creation_id)
        
        if status == "ERROR":
            print("An error occurred while processing the media.")
            return False
        
        print("Media is being processed by Instagram, waiting 15 seconds...")
        time.sleep(15)
        retry_count += 1
    
    print("Operation timed out.")
    return False

def upload_media(media_type, media_url, caption=None):
    """Initiates and completes the process of uploading Reels or Stories."""
    print(f"New upload request: Type={media_type}, URL={media_url}")
    api_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media"
    params = {'access_token': ACCESS_TOKEN}

    if media_type == 'reel':
        params.update({'media_type': 'REELS', 'video_url': media_url, 'caption': caption or "Uploaded with Python! 🚀", 'share_to_feed': 'true'})
    elif media_type == 'image_story':
        params.update({'media_type': 'STORIES', 'image_url': media_url})
    elif media_type == 'video_story':
        params.update({'media_type': 'STORIES', 'video_url': media_url})
    else:
        return {'status': 'error', 'message': 'Invalid media type.'}

    print("Step 1: Creating media container...")
    try:
        response = requests.post(api_url, params=params)
        response.raise_for_status()
        result = response.json()

        if 'id' in result:
            creation_id = result['id']
            print(f"Container created successfully: {creation_id}. Starting publishing process...")
            
            success = process_and_publish_media(creation_id)
            if success:
                return {'status': 'success', 'message': 'Media published successfully!'}
            else:
                return {'status': 'error', 'message': 'An error occurred during media processing or publishing.'}
        else:
            return {'status': 'error', 'message': f"API Error (Container): {result.get('error', {}).get('message', 'Unknown error')}"}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"Critical API Error: {error_details}"}


# ==============================================================================
# COMMENT MANAGEMENT FUNCTIONS
# ==============================================================================

def get_latest_posts():
    """Fetches the last 25 posts from the account."""
    print("Fetching latest posts from the account...")
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
            return {'status': 'success', 'message': 'No posts found on the account.', 'data': []}
        
        return {'status': 'success', 'data': posts}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"An error occurred while fetching posts: {error_details}"}

def get_comments_for_post(media_id):
    """Fetches comments for a specific media_id."""
    print(f"Fetching comments for post with ID: '{media_id}'...")
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
            return {'status': 'success', 'message': 'There are no comments on this post.', 'data': []}
            
        return {'status': 'success', 'data': comments}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"An error occurred while fetching comments: {error_details}"}

def reply_to_comment(comment_id, message):
    """Sends a reply to a specific comment_id."""
    print(f"Sending reply to comment with ID '{comment_id}': {message}")
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
            return {'status': 'success', 'message': 'Reply sent successfully.'}
        else:
            return {'status': 'error', 'message': f"Could not send reply: {result}"}
    except requests.exceptions.RequestException as e:
        error_details = e.response.json() if e.response else str(e)
        return {'status': 'error', 'message': f"An error occurred while sending the reply: {error_details}"}