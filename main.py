import tweepy
import time

# Twitter API credentials
client = tweepy.Client(
    bearer_token='AAAAAAAAAAAAAAAAAAAAACJkxQEAAAAAeMQafWj8B3ipZgXFzqqjdTDIXhA%3DwVrt7ZNaYAdVgovYtsKhv5qbIOQHtZ9Iy6LeCjAFQzIxjCRmV0',
    consumer_key='JU9roAfJIzPFrS6AkTgiDUd4K',
    consumer_secret='Vu01eFKoL4TbyyXTt3V7HfZ8m9XBAwu42fgsvIcZuupQd1Drkg',
    access_token='1864180044115136513-k2KEGgIG6xjIql9FtIYXCAZZeIajBW',
    access_token_secret='2r1GgQNtwJCXu9YpTxiPLjcmyf83FSiSYl0gmoqPNUHA7'
)

# Function to reply to mentions
def reply_to_mentions():
    try:
        # Search for tweets mentioning your username
        query = "@WhatsHerAt_ -is:retweet"
        mentions = client.search_recent_tweets(query=query, max_results=10) # limits search to 10 tweets

        if mentions.data:
            for tweet in mentions.data:
                print(f"New mention from @{tweet.author_id}: {tweet.text}")
                try:
                    # Reply to the mention
                    reply_text = f"Hello! Thanks for the mention!"
                    client.create_tweet(
                        text=reply_text,
                        in_reply_to_tweet_id=tweet.id
                    )
                    print("Replied successfully!")
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
