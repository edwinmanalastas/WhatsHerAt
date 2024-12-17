import os
import time
import json
import re
from collections import Counter
from dotenv import load_dotenv

import tweepy
import cv2
from io import BytesIO
from PIL import Image
from deepface import DeepFace
import requests
from bs4 import BeautifulSoup
import glob

load_dotenv()
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

# X API credentials
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET
)

# file to store processed tweet IDs
PROCESSED_TWEETS_FILE = "processed_tweets.json"

# Load processed tweet IDs from the file
def load_processed_tweets():
    if os.path.exists(PROCESSED_TWEETS_FILE) and os.path.getsize(PROCESSED_TWEETS_FILE) > 0:
        with open(PROCESSED_TWEETS_FILE, "r") as file:
            return set(json.load(file))
    else:
        # If file does not exist or is empty, return an empty set
        return set()

# Save processed tweet IDs to the file
def save_processed_tweets(tweet_ids):
    with open(PROCESSED_TWEETS_FILE, "w") as file:
        json.dump(list(tweet_ids), file)

# Function to fetch original tweet details
def reply_to_mentions():
    processed_tweets = load_processed_tweets()

    try:
        # Search for tweets mentioning your username
        query = "@WhatsHerAt_ -is:retweet"
        mentions = client.search_recent_tweets(
            query=query,
            max_results=10,
            tweet_fields=["author_id", "conversation_id", "referenced_tweets"]
        )

        if mentions.data:
            for tweet in mentions.data:
                # Skip tweets already processed
                if tweet.id in processed_tweets:
                    continue
                try:
                    
                    # Check if the tweet is a reply and get the parent tweet ID                    
                    referenced_tweet_id = next(
                        (ref_tweet["id"] for ref_tweet in tweet.referenced_tweets if ref_tweet["type"] == "replied_to"), 
                        None
                    )

                    # Fetch the original tweet's details if it's a reply
                    if referenced_tweet_id:
                        original_tweet = client.get_tweet(
                            referenced_tweet_id, 
                            expansions=["author_id", "attachments.media_keys"], 
                            media_fields=["url", "type", "variants"]
                        )

                        original_author = original_tweet.includes["users"][0]
                        original_tweet_link = f"https://x.com/{original_author.username}/status/{referenced_tweet_id}"
                        print(f"Original tweet being replied to: {original_tweet_link}")
                        print(f"Processing media from: {original_tweet_link}")

                        #delete before
                        cleanup_old_files()

                        media_urls = []
                        if original_tweet.includes and 'media' in original_tweet.includes:
                            for media in original_tweet.includes['media']:
                                print("Media found:", media)  # Debug: Print media to check content
                                if media['type'] == 'photo':  # If the media is a photo
                                    media_urls.append({'url': media['url'], 'type': 'image'})
                                elif media['type'] == 'video':  # If the media is a video
                                    # Check if 'variants' exists in the media data
                                    if 'variants' in media:
                                        # Find the video with the highest quality (highest bitrate)
                                        video_url = max(media['variants'], key=lambda x: x.get('bitrate', 0))['url']
                                        media_urls.append({'url': video_url, 'type': 'video'})
                                else:
                                    print(f"Unsupported media type or missing variants for media {media['media_key']}.")
                        
                        if not media_urls:
                            print(f"No media URLs found in tweet ID {tweet.id}. Includes: {mentions.includes.get('media', [])}")

                        downloaded_media_path = None
                        if media_urls:
                            for index, media in enumerate(media_urls):
                                download_path = f"media_{index + 1}"
                                #download_path = f"media"
                                
                                # Handle download for images
                                if media['type'] == 'image':
                                    download_path += '.jpg'  # Save images as .jpg files
                                elif media['type'] == 'video':
                                    download_path += '.mp4'  # Save videos as .mp4 files

                                downloaded_media_path = download_media(media['url'], media['type'], download_path)
                        else:
                            print("No media found to download")
                        
                         # Extract a timestamp if mentioned in the tweet (e.g., "0:39")
                        tweet_text = tweet.text
                        start_time = None
                        timestamp_match = re.search(r'\b(\d+):(\d{2})\b', tweet_text)
                        if timestamp_match:
                            start_time = timestamp_match.group(0)
                            print(f"Extracted start time from tweet: {start_time}")

                        if downloaded_media_path:
                            if downloaded_media_path.endswith('.mp4'):
                                process_video(downloaded_media_path, start_time=start_time)  # Pass start time
                            elif downloaded_media_path.endswith(('.jpg', '.png')):
                                process_image(downloaded_media_path)  # Process the image
                            else:
                                print("Unsupported media type.")
                        else:
                            print("No media found to download.2")

                        image_path = "./face.jpg"
                        urls = facecheck(image_path)
                        result = findname(urls)

                    else:
                        print("This tweet is not a reply to another tweet.")
                    
                    # Reply to the mention
                    reply_text = f"{result}"
                    client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=tweet.id
                    )
                    print("Replied successfully!")
   
                    # Add the tweet ID to the set of processed tweets
                    processed_tweets.add(tweet.id)
                    save_processed_tweets(processed_tweets)

                except Exception as e:
                    print(f"Error while processing: {e}")
        else:
            print("No new mentions found.")

    except tweepy.errors.TooManyRequests as e:
        print("Rate limit reached. Waiting to reset...")
        reset_time = int(e.response.headers.get("x-rate-limit-reset", time.time() + 900))
        sleep_time = reset_time - int(time.time())
        print(f"Sleeping for {sleep_time} seconds.")
        time.sleep(max(sleep_time, 0))  # Wait until the limit resets

# Function to process the image, detect faces, and filter by gender
def process_image(image_path):
    min_dim = 60
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Failed to load image from {image_path}.")
        return
    
    woman_detected = False
    try:
        analysis = DeepFace.analyze(image, actions=['gender'], enforce_detection=False)
        for face in analysis:
            gender = face['dominant_gender']
            print(f"Detected {gender} in the image.")
            if gender == 'Woman':
                woman_detected = True
                print("Saving the woman's face...")
                region = face['region']
                x, y, w, h = safe_extract_with_padding(region, image)
                if w > 0 and h > 0:
                    cropped_face = image[y:y+h, x:x+w]
                    if cropped_face.shape[0] < min_dim or cropped_face.shape[1] < min_dim:
                        cropped_face = cv2.resize(cropped_face, (min_dim, min_dim))
                    face_filename = 'face.jpg'
                    cv2.imwrite(face_filename, cropped_face)
                    print(f"Saved face as {face_filename}")
                else:
                    print("Invalid face region dimensions. Skipping cropping.")
        if not woman_detected:
            print("No woman was detected in the image.")
    except Exception as e:
        print(f"Error during face analysis: {e}")


# Function to process the video and detect faces in each frame
def process_video(video_path, start_time=None):
    min_dim = 60
    # Open the video file
    video_capture = cv2.VideoCapture(video_path)

    if not video_capture.isOpened():
        print(f"Error: Unable to open video file {video_path}.")
        return

    # If a start time is provided, set the video position
    if start_time:
        # Convert the start time (e.g., "0:39") to milliseconds
        try:
            minutes, seconds = map(int, start_time.split(":"))
            start_ms = (minutes * 60 + seconds) * 1000
            video_capture.set(cv2.CAP_PROP_POS_MSEC, start_ms)
            print(f"Starting video processing at timestamp {start_time} ({start_ms} ms).")
        except ValueError:
            print("Invalid start time format. Use MM:SS format.")
            return

    frame_count = 0
    first_woman_detected = False  # Flag to check if a woman has already been detected

    while True:
        # Read the next frame from the video
        ret, frame = video_capture.read()
        if not ret:
            break  # End of video

        frame_count += 1
        print(f"Processing frame {frame_count}...")

        # Use DeepFace to analyze the frame for faces and gender
        try:
            analysis = DeepFace.analyze(frame, actions=['gender'], enforce_detection=False)

            # Filter by gender: Check if the detected person is a woman
            for face in analysis:
                gender = face['dominant_gender']
                print(f"Detected {gender} in the frame.")

                # If the face is of a woman and no woman has been detected before
                if gender == 'Woman' and not first_woman_detected:
                    print("Saving the woman's face...")

                    # Extract the face coordinates safely
                    region = face['region']
                    # print("Face region details:", region)

                    # Safely extract x, y, w, h values with defaults in case keys are missing         
                    x, y, w, h = safe_extract_with_padding(region, frame)

                    # Check if the dimensions are valid (non-zero width and height)
                    if w > 0 and h > 0:

                        # Crop the face from the frame
                        cropped_face = frame[y:y+h, x:x+w]

                        # Resize if the cropped face is smaller than 60x60
                        if cropped_face.shape[0] < min_dim or cropped_face.shape[1] < min_dim:
                            cropped_face = cv2.resize(cropped_face, (min_dim, min_dim))

                        # Save the cropped face as a new image
                        face_filename = f"face.jpg"
                        cv2.imwrite(face_filename, cropped_face)
                        print(f"Saved face as {face_filename}")

                        first_woman_detected = True

                        print("First woman's face detected. Stopping video processing.")
                        break

        except Exception as e:
            print(f"Error during face analysis in frame {frame_count}: {e}")

        if first_woman_detected:
            break
    if not first_woman_detected:
        print("No woman was detected in the video.")
    # Release the video capture object
    video_capture.release()
    print("Video processing complete.")

# Safely extract x, y, w, h values with padding and ensure they are within bounds
def safe_extract_with_padding(region, image, min_dim=60, padding=10):
    img_h, img_w, _ = image.shape
    x = max(region.get('x', 0) - padding, 0)
    y = max(region.get('y', 0) - padding, 0)
    w = region.get('w', 0) + 2 * padding
    h = region.get('h', 0) + 2 * padding
    w = min(w, img_w - x)
    h = min(h, img_h - y)
    if w < min_dim:
        w = min_dim
    if h < min_dim:
        h = min_dim
    return x, y, w, h


def findname(urls):
    # Function to extract text from a webpage
    def extract_text(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            texts = soup.stripped_strings
            return ' '.join(texts)
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return ""

    # Function to extract name-like sequences (2-3 words starting with capital letters)
    def extract_names(text):
        pattern = r'\b([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})\b'
        # pattern = r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)?)\b'
        matches = re.findall(pattern, text)
        return matches

    # Scrape each link and collect potential names
    all_names = []

    counter = 0
    print()

    for url in urls:
        text = extract_text(url)
        potential_names = extract_names(text)
        all_names.extend(potential_names)
        counter += 1
        print("Going through " + str(counter) + " of " + str(len(urls)))
        # print(counter)

    # Normalize names (convert to lowercase for counting consistency)
    normalized_names = [name.lower() for name in all_names]

    # Count the frequency of each name
    name_counts = Counter(normalized_names)

    # Sort and display the most common names
    most_common_names = name_counts.most_common(10)

    # prints lists of common names
    #for name, count in most_common_names:
        #print(f"{name.title()}: {count}")

    # Load female names from the file
    with open('names.txt', 'r') as file:
        female_names = set(name.strip().lower() for name in file.readlines())

    # Check which of the most common names are likely female names
    female_name_results = []
    for name, count in most_common_names:
        # if any(part in female_names for part in name.split()):
        if name.split()[0].lower() in female_names:
            female_name_results.append((name.title(), count))

    # Display the female names with counts
    # print("\nMost common female name:")
    for name, count in female_name_results:
        return name

def facecheck(image_file):
    TESTING_MODE = True
    load_dotenv()
    APITOKEN = os.getenv("FACECHECK_API_TOKEN")

    def search_by_face(image_file):
        if TESTING_MODE:
            print('****** TESTING MODE search, results are inacurate, and queue wait is long, but credits are NOT deducted ******')

        site='https://facecheck.id'
        headers = {'accept': 'application/json', 'Authorization': APITOKEN}
        files = {'images': open(image_file, 'rb'), 'id_search': None}
        response = requests.post(site+'/api/upload_pic', headers=headers, files=files).json()

        if response['error']:
            return f"{response['error']} ({response['code']})", None

        id_search = response['id_search']
        print(response['message'] + ' id_search='+id_search)
        json_data = {'id_search': id_search, 'with_progress': True, 'status_only': False, 'demo': TESTING_MODE}

        while True:
            response = requests.post(site+'/api/search', headers=headers, json=json_data).json()
            if response['error']:
                return f"{response['error']} ({response['code']})", None
            if response['output']:
                return None, response['output']['items']
            print(f'{response["message"]} progress: {response["progress"]}%')
            time.sleep(1)


    # Search the Internet by face
    error, urls_images = search_by_face(image_file)

    urls = [] 

    if urls_images:
        for im in urls_images:      # Iterate search results
            score = im['score']     # 0 to 100 score how well the face is matching found image
            url = im['url']         # url to webpage where the person was found
            image_base64 = im['base64']     # thumbnail image encoded as base64 string
            #print(f"{score} {url} {image_base64[:32]}...")
            urls.append(url)
            if len(urls) >= 10:
                break
    else:
        print(error)
    
    return urls

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
        return download_path
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None

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
    return output_filename

def cleanup_old_files():
    # Remove all media files (e.g., media_1.mp4, media_2.mp4, etc.)
    for file_path in glob.glob("media_*.mp4"):
        try:
            os.remove(file_path)
            print(f"Deleted old file: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

    # Remove face.jpg if it exists
    face_path = "face.jpg"
    if os.path.exists(face_path):
        os.remove(face_path)
        print(f"Deleted old file: {face_path}")

# Continuously check for new mentions
while True:
    reply_to_mentions()
    break