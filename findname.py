import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import time
from facecheck import urls  # Import urls from facecheck.py

# Function to extract text from a webpage
def extract_text(url, timeout=10):
    try:
        start_time = time.time()  # Start the timer
        response = requests.get(url, timeout=timeout)  # Timeout in seconds
        response.raise_for_status()
        elapsed_time = time.time() - start_time  # Measure elapsed time
        print(f"Scraped {url} in {elapsed_time:.2f} seconds")
        soup = BeautifulSoup(response.text, 'html.parser')
        texts = soup.stripped_strings
        return ' '.join(texts)
    except requests.Timeout:
        print(f"Timeout occurred for {url} after {timeout} seconds. Skipping...")
        return ""
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

# Measure average scrape time
scrape_times = []

for url in urls:
    start_time = time.time()
    text = extract_text(url)
    elapsed_time = time.time() - start_time

    # Record scrape time and calculate average
    scrape_times.append(elapsed_time)
    average_scrape_time = sum(scrape_times) / len(scrape_times)
    
    # Skip if the scrape time exceeds the average by a factor (e.g., 1.5x)
    if elapsed_time > average_scrape_time * 1.5:
        print(f"Skipping {url} due to long scrape time ({elapsed_time:.2f}s > average {average_scrape_time:.2f}s)")
        continue

    potential_names = extract_names(text)
    all_names.extend(potential_names)
    counter += 1
    print(f"Processed {counter} of {len(urls)} URLs")

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
    # print(f"{name}: {count}")
    print(f"{name}")
    break