import tweepy
import requests
from io import BytesIO
from PIL import Image
import os

# Twitter API credentials
client = tweepy.Client(
    bearer_token='AAAAAAAAAAAAAAAAAAAAACJkxQEAAAAAeMQafWj8B3ipZgXFzqqjdTDIXhA%3DwVrt7ZNaYAdVgovYtsKhv5qbIOQHtZ9Iy6LeCjAFQzIxjCRmV0',
    consumer_key='JU9roAfJIzPFrS6AkTgiDUd4K',
    consumer_secret='Vu01eFKoL4TbyyXTt3V7HfZ8m9XBAwu42fgsvIcZuupQd1Drkg',
    access_token='1864180044115136513-k2KEGgIG6xjIql9FtIYXCAZZeIajBW',
    access_token_secret='2r1GgQNtwJCXu9YpTxiPLjcmyf83FSiSYl0gmoqPNUHA7'
)

# Function to extract media URL from tweet URL
def extract_media_url_from_tweet(tweet_url):
    try:
        tweet_id = tweet_url.split('/')[-1]  # Extract tweet ID from the URL
        tweet = client.get_tweet(tweet_id, expansions='attachments.media_keys', media_fields='url')
        
        if tweet.includes.get('media', []):
            media = tweet.includes['media'][0]
            media_url = media['url']
            return media_url
        else:
            print("No media found in the tweet.")
            return None
    except Exception as e:
        print(f"Error extracting media URL: {e}")
        return None

# Function to download an image from a given URL and save it locally
def download_image(media_url, download_path):
    try:
        # Send the GET request to the media URL
        response = requests.get(media_url)
        response.raise_for_status()  # Raise an error if the request fails
        img_data = BytesIO(response.content)

        # Open and save the image
        img = Image.open(img_data)
        img.save(download_path)
        print(f"Image downloaded and saved to {download_path}")
        return True
    except Exception as e:
        print(f"Error downloading media: {e}")
        return False

if __name__ == "__main__":
    # Test tweet URL
    tweet_url = 'https://x.com/Google/status/1823411426024710388/photo/1'  # Replace with the tweet URL for testing
    
    # Extract media URL from the tweet
    media_url = extract_media_url_from_tweet(tweet_url)
    
    if media_url:
        download_path = 'downloaded_image.jpg'  # Path to save image
        # Test the download function
        download_image(media_url, download_path)