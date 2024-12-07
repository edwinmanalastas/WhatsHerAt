import os
import time
import json
import re
from collections import Counter
from dotenv import load_dotenv

import tweepy
import yt_dlp
import cv2
from deepface import DeepFace
import requests
from bs4 import BeautifulSoup

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

# file to store processed tweet IDs
PROCESSED_TWEETS_FILE = "processed_tweets.json"
REPLIED_TWEETS_FILE = "replied_tweets.json"

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
                    referenced_tweet_id = None
                    if tweet.referenced_tweets:
                        for ref_tweet in tweet.referenced_tweets:
                            if ref_tweet["type"] == "replied_to":
                                referenced_tweet_id = ref_tweet["id"]

                    # Fetch the original tweet's details if it's a reply
                    if referenced_tweet_id:
                        original_tweet = client.get_tweet(
                            referenced_tweet_id, expansions="author_id"
                        )
                        original_author = original_tweet.includes["users"][0]
                        original_tweet_link = f"https://twitter.com/{original_author.username}/status/{referenced_tweet_id}"
                        print(f"Original tweet being replied to: {original_tweet_link}")

                        print(f"Processing media from: {original_tweet_link}")
                        # Download media using yt-dlp
                        downloaded_media_path = download_twitter_media(original_tweet_link, output_filename="media")

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
                            print("No media found to download.")

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


# Function to download Twitter media using yt-dlp
def download_twitter_media(tweet_url, output_filename="media"):
    """
    Downloads media (videos/images) from a given Twitter URL using yt-dlp.
    """
    ydl_opts = {
        'outtmpl': f'{output_filename}.%(ext)s',  # Save as "media.<extension>" in the current folder
        'format': 'bestvideo+bestaudio/best',  # Download the best quality video with audio
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([tweet_url])
        print(f"Media downloaded successfully and saved as {output_filename}.")
        return f"{output_filename}.mp4"  # Return the downloaded file path
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None


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
    with open('females.txt', 'r') as file:
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

# Continuously check for new mentions
while True:
    reply_to_mentions()
    time.sleep(300)  # Check every 5 minutes