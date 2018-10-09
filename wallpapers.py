import os
import json
from datetime import datetime
import webbrowser
import praw
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

wallpaper_subreddits = ['wallpaper','wallpapers','spaceporn','earthporn','skyporn','waterporn','botanicalporn']
credentials_file = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
API_URL = 'https://photoslibrary.googleapis.com/v1/'


def get_authentication_services():
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
    credentials = flow.run_local_server()
    oauth_token = 'Bearer {}'.format(credentials.token)
    return oauth_token

def getImageUrls():
    client_id = "YOUR-CLIENT-ID"
    client_secret = "YOUR-CLIENT-SECRET"
    user_agent = "My user agent"
    acceptable_links = ['https://i.redd.it','https://imgur.com']
    reddit = praw.Reddit(client_id=client_id,client_secret=client_secret,user_agent=user_agent)
    image_urls = []
    for subreddit in wallpaper_subreddits:
        for submission in reddit.subreddit(subreddit).hot(limit=5):
            url = submission.url
            if any(link in url for link in acceptable_links):
                image_urls.append(url)
    return image_urls

def getImage(url):
    # download the image
    # return the images in raw bytes
    r = requests.get(url)
    return r.content

def createAlbum(oauth_token,endpoint):
    # return albumId
    date = datetime.today().strftime('%m/%d/%Y')
    album_title = "Screensaver {}".format(date)
    headers = {"Content-type":"application/json","Authorization":oauth_token}
    body = { "album": {"title" : album_title}}
    body = json.dumps(body)
    url = getApiUrl(endpoint)
    resp = requests.post(url,headers=headers,data=body)
    resp = json.loads(resp.content)
    return resp['id']

def getAlbum(oauth_token,endpoint,album_id):
    headers = {"Content-type":"application/json","Authorization":oauth_token}
    url = getApiUrl(endpoint,album_id)
    resp = requests.get(url,headers=headers)
    resp = json.loads(resp.content)
    return resp

def uploadRawImage(oauth_token,raw_bytes,endpoint):
    # post request: upload media binary data
    # return upload token
    headers = {"Content-type":"application/octet-stream","Authorization" : oauth_token,"X-Goog-Upload-File-Name":"test","X-Goog-Upload-Protocol":"raw"}
    url = getApiUrl(endpoint)
    resp = requests.post(url,headers=headers,data=raw_bytes)
    return resp.content

def createMediaItem(oauth_token,album_id,upload_tokens,endpoint):
    newMediaItems = []
    for token in upload_tokens:
        newMediaItems.append({"simpleMediaItem":{"uploadToken":token}})
    headers ={"Content-type" : "application/json", "Authorization" : oauth_token}
    body = {"albumId": album_id,"newMediaItems":newMediaItems}
    body = json.dumps(body)
    url = getApiUrl(endpoint)
    resp = requests.post(url,headers=headers,data=body)
    resp = json.loads(resp.content)
    return resp

def getApiUrl(endpoint,id=None):
    if id is not None:
        return "{0}{1}/{2}".format(API_URL,endpoint,id)
    else :
        return "{0}{1}".format(API_URL,endpoint)


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    urls = getImageUrls()
    print ('Recieved urls from reddit.')
    oauth_token = get_authentication_services()
    print('Client successfully authenticated.')
    album_id = createAlbum(oauth_token,'albums')
    print ('Album successfully created.')
    upload_tokens = []
    for url in urls:
        raw_image = getImage(url)
        token = uploadRawImage(oauth_token,raw_image,'uploads')
        upload_tokens.append(token)

    mediaItemsResponse = createMediaItem(oauth_token,album_id,upload_tokens,'mediaItems:batchCreate')
    album = getAlbum(oauth_token,'albums',album_id)
    print('Successfully uploaded {0} photos to album {1}. \n'.format(album['mediaItemsCount'],album['title']))
    webbrowser.open_new_tab(album['productUrl'])
