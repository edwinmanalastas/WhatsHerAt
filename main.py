import tweepy
import time
from dotenv import load_dotenv
import os
import json

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

# file to store replied tweet IDs
REPLIED_TWEETS_FILE = "replied_tweets.json"

# Load replied tweet IDs from the file
def load_replied_tweets():
    if os.path.exists(REPLIED_TWEETS_FILE) and os.path.getsize(REPLIED_TWEETS_FILE) > 0:
        with open(REPLIED_TWEETS_FILE, "r") as file:
            return set(json.load(file))
    else:
        # If file does not exist or is empty, return an empty set
        return set()
    
# Save replied tweet IDs to the file
def save_replied_tweets(tweet_ids):
    with open(REPLIED_TWEETS_FILE, "w") as file:
        json.dump(list(tweet_ids), file)

# Function to reply to mentions
def reply_to_mentions():
    replied_tweets = load_replied_tweets()

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
                # Skip tweets already replied to
                if tweet.id in replied_tweets:
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
                    else:
                        print("This tweet is not a reply to another tweet.")

                    # Reply to the mention
                    reply_text = f"Hello! Thanks for the mention!"
                    client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=tweet.id
                    )
                    print("Replied successfully!")

                    # Add the tweet ID to the set of replied tweets
                    replied_tweets.add(tweet.id)
                    save_replied_tweets(replied_tweets)

                except Exception as e:
                    print(f"Error while replying: {e}")
        else:
            print("No new mentions found.")

    except tweepy.errors.TooManyRequests as e:
        print("Rate limit reached. Waiting to reset...")
        reset_time = int(e.response.headers.get("x-rate-limit-reset", time.time() + 900))
        sleep_time = reset_time - int(time.time())
        print(f"Sleeping for {sleep_time} seconds.")
        time.sleep(max(sleep_time, 0))  # Wait until the limit resets

# Continuously check for new mentions
while True:
    reply_to_mentions()
    time.sleep(300)  # Check every 5 minutes
