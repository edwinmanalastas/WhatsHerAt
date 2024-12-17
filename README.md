# Twitter Media Bot with Facial Recognition

## Project Overview
This project implements a **Twitter bot** that replies to mentions by:
- Downloading media (images/videos) from Twitter posts.
- Performing **facial recognition** on the media using DeepFace to detect gender.
- Identifying related online profiles (e.g., Instagram) using a face recognition API.
- Scraping associated web pages to extract **common names** based on detected links.

The bot is capable of processing media in under 30 seconds and provides an automated response to mentions.

---

## Key Features
- **Twitter Integration**: Interacts with the Twitter API to search mentions and download media.
- **Facial Recognition**: Analyzes images and video frames to detect faces and identify gender using DeepFace.
- **Face Search API**: Uploads detected faces to an external API (FaceCheck) to find matching profiles.
- **Web Scraping**: Scrapes URLs associated with detected profiles to extract likely names.
- **Robust Media Handling**: Supports downloading and processing both images and videos, with timestamp extraction for videos.
- **Efficient Workflow**: Keeps track of processed tweets to avoid duplication and optimize processing time.
- **Custom Timestamp Detection**: Users can include a timestamp (e.g., @WhatsHerAt_ 0:46) in their mention, and the bot will process the video starting from the specified time, allowing faster face detection.
- **Simple Trigger for Testing**: To test the bot, users can simply tweet or reply with a mention like @WhatsHerAt_. The bot automatically processes the media and searches for matching results.

---

## Tech Stack
- **Python**: Core programming language.
- **Tweepy**: For Twitter API integration.
- **OpenCV**: Processes local images and videos.
- **DeepFace**: Detects and analyzes faces and gender.
- **BeautifulSoup**: Scrapes web pages for relevant content.
- **FaceCheck API**: Performs internet-wide face matching.
- **PIL**: Image handling and processing.
- **dotenv**: Manages environment variables securely.
- **Requests**: Handles HTTP requests for media downloads.

---

## Project Structure
```
project-folder/
├── main.py                   # Main script integrating all functionalities
├── requirements.txt          # Required Python dependencies
├── processed_tweets.json     # Stores IDs of processed tweets
├── scripts/                  # Modular components for individual use
│   ├── facecheck.py          # Handles face upload and API calls
│   ├── findname.py           # Scrapes URLs to find common names
│   ├── process_local.py      # Detects faces in local media
│   └── twitter_downloader.py # Downloads Twitter media files
├── .env                      # Environment variables (keys/secrets)
├── .gitignore                # Excludes sensitive or redundant files
└── README.md                 # Project documentation
```

---

## Installation
### Prerequisites
1. Python 3.x installed
2. Twitter Developer Account (API credentials)
3. FaceCheck API Token (for facial recognition)
4. OpenCV dependencies (for media processing)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/edwinmanalastas/WhatsHerAt-TwitterBot.git
   cd twitter-media-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file and add your API keys/secrets:
   ```
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   TWITTER_CONSUMER_KEY=your_consumer_key
   TWITTER_CONSUMER_SECRET=your_consumer_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   FACECHECK_API_TOKEN=your_facecheck_api_token
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

---

## Usage
1. Mention the bot's username on Twitter with a post containing an image or video.
2. If a face is detected, the bot will reply with the likely name extracted from profile links.
3. Logs will display processing status, including media downloads and analysis results.

---

## Additional Scripts
These scripts can be used independently for specific tasks:

| Script                 | Description                                      |
|------------------------|--------------------------------------------------|
| `facecheck.py`         | Uploads images to the FaceCheck API for recognition. |
| `findname.py`          | Scrapes URLs to extract the most common names.   |
| `process_local.py`     | Detects and processes faces in local images/videos. |
| `twitter_downloader.py`| Downloads media files (images/videos) from Twitter links. |

To run a script individually, for example `facecheck.py`:
```bash
python scripts/facecheck.py --image path/to/image.jpg
```

---

## Known Issues
- Twitter API rate limits can delay responses. Is only able to reply to one mention every 15 minutes
- FaceCheck API may take longer and is inacurrate in testing mode.

---

## Future Improvements
- Add support for multiple face detection in a single media file.
- Enhance web scraping to improve name accuracy.
- Optimize video processing for longer durations.

---

## Disclaimer
This bot is intended for educational purposes only. Use responsibly and ensure compliance with Twitter's Developer Policies and privacy standards.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contributions
Contributions are welcome! If you find bugs or want to improve features:
1. Fork the repository.
2. Create a new branch.
3. Submit a pull request.

---

## Author
**Edwin Manalastas**
- [GitHub](https://github.com/edwinmanalastas)
- [LinkedIn](https://www.linkedin.com/in/edwin-manalastas/)
- [Portfolio](https://edwinmanalastas.github.io)

---