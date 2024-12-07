import time
import requests
from dotenv import load_dotenv
import os

TESTING_MODE = True
load_dotenv()
APITOKEN = os.getenv("FACECHECK_API_TOKEN")

# Download the photo of the person you want to find
image_file = './face.jpg' 

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

        #if score > 80:
            #urls.append(url)
            
        if len(urls) >= 10:
            break
else:
    print(error)