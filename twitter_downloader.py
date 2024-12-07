import tweepy
import requests
import time
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# Twitter API credentials
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)
# Function to extract media URL from tweet URL
def extract_media_url_from_tweet(tweet_url):
    try:
        # Extract the tweet ID correctly from the URL (removes anything after /status/)
        tweet_id = tweet_url.split('/status/')[-1].split('/')[0]  # Extract only the tweet ID part
        print(f"Extracted tweet ID: {tweet_id}")  # Debug: Check the tweet ID

        tweet = client.get_tweet(
            tweet_id, 
            expansions='attachments.media_keys', 
            media_fields='url,variants'  # Use 'variants' instead of 'video_info'
        )
        
        # Debug: Print the whole tweet response to check the structure
        print("Tweet Response:", tweet)
        
        media_urls = []

        if tweet.includes and 'media' in tweet.includes:
            for media in tweet.includes['media']:
                # print("Media found:", media)  # Debug: Print media to check content
                if media['type'] == 'photo':  # If the media is a photo
                    media_urls.append({'url': media['url'], 'type': 'image'})
                elif media['type'] == 'video':  # If the media is a video
                    # Check if 'variants' exists in the media data
                    if 'variants' in media:
                        # Find the video with the highest quality (highest bitrate)
                        video_url = max(media['variants'], key=lambda x: x.get('bitrate', 0))['url']
                        media_urls.append({'url': video_url, 'type': 'video'})
                    else:
                        print(f"Video variants not available for media {media['media_key']}")
            return media_urls
        else:
            print("No media found in the tweet.")
            return None
    except tweepy.errors.TooManyRequests as e:
        print("Rate limit reached. Waiting to reset...")
        reset_time = int(e.response.headers.get("x-rate-limit-reset", time.time() + 900))
        sleep_time = reset_time - int(time.time())
        print(f"Sleeping for {sleep_time} seconds.")
        time.sleep(max(sleep_time, 0))  # Wait until the limit resets
    
# Function to download an image from a given URL and save it locally
def download_media(media_url, media_type, download_path):
    try:
        # Download the media (image or video)
        response = requests.get(media_url)
        response.raise_for_status()  # Raise an error if the request fails

        if media_type == 'image':
            # Save the image
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img.save(download_path)
            print(f"Image downloaded and saved to {download_path}")
        elif media_type == 'video':
            # Check if the video is a single MP4 or multipart (m4s)
            if "m3u8" in media_url or "container=fmp4" in media_url:
                print("Video is multipart, downloading in parts.")
                download_parts(media_url, download_path)
            else:
                # Save the simple MP4 video
                with open(download_path, 'wb') as f:
                    f.write(response.content)
                print(f"Video downloaded and saved to {download_path}")
        return True
    except Exception as e:
        print(f"Error downloading media: {e}")
        return False

# Function to download video parts if it's a multipart m4s video
def download_parts(url, output_filename):
    video_part_prefix = "https://video.twimg.com"

    # Get the video part URL from the container
    resp = requests.get(url, stream=True)
    pattern = re.compile(r'(/[^\n]*/(\d+x\d+)/[^\n]*container=fmp4)')
    matches = pattern.findall(resp.text)

    # Choose the best resolution
    max_res = 0
    max_res_url = None
    for match in matches:
        url, resolution = match
        width, height = resolution.split('x')
        res = int(width) * int(height)
        if res > max_res:
            max_res = res
            max_res_url = url

    assert max_res_url is not None, f'Failed to find a video part URL from {url}'

    # Now download the chosen video part
    resp = requests.get(video_part_prefix + max_res_url, stream=True)
    mp4_pattern = re.compile(r'(/[^\n]*\.mp4)')
    mp4_parts = mp4_pattern.findall(resp.text)

    assert len(mp4_parts) == 1, f'Multiple MP4 parts found, expected only 1. Tweet URL: {url}'

    mp4_url = video_part_prefix + mp4_parts[0]
    m4s_part_pattern = re.compile(r'(/[^\n]*\.m4s)')
    m4s_parts = m4s_part_pattern.findall(resp.text)

    # Save the video part
    with open(output_filename, 'wb') as f:
        r = requests.get(mp4_url, stream=True)
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()

        for part in m4s_parts:
            part_url = video_part_prefix + part
            r = requests.get(part_url, stream=True)
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

    print(f"Video downloaded and saved to {output_filename}")
    return True

if __name__ == "__main__":
    # Test tweet URL
    tweet_url = 'https://x.com/elonmusk/status/1863623453045039399'  # Replace with the tweet URL for testing
    
    # Extract media URL from the tweet
    media_urls = extract_media_url_from_tweet(tweet_url)
    
    if media_urls:
        for index, media in enumerate(media_urls):
            download_path = f"downloaded_media_{index + 1}"
            
            # Handle download for images
            if media['type'] == 'image':
                download_path += '.jpg'  # Save images as .jpg files
            elif media['type'] == 'video':
                download_path += '.mp4'  # Save videos as .mp4 files
            
            # Test the download function
            download_media(media['url'], media['type'], download_path)
    else:
        print("No media found to download.")
