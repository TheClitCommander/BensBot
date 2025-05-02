#!/usr/bin/env python3
import os
import requests
import json
from datetime import datetime

# NYTimes API key
API_KEY = "NosApZGLGvPusEz30Fk4lQban19z9PTo"

# API endpoint
url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"

# Parameters
params = {
    'q': 'AAPL',
    'api-key': API_KEY,
    'sort': 'newest',
    'page': 0
}

# Make the request
print(f"Testing NYTimes API with key: {API_KEY}")
print(f"Making request to: {url}")

try:
    response = requests.get(url, params=params, timeout=10)
    
    # Check response
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('response', {}).get('docs', [])
        
        print(f"Success! Retrieved {len(articles)} articles")
        
        # Print first article title if available
        if articles:
            first_article = articles[0]
            title = first_article.get('headline', {}).get('main', 'No title')
            print(f"First article title: {title}")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Error: {str(e)}")

print("\nNow testing Mediastack API")
MEDIASTACK_API_KEY = "3ff958493e0f1d8cf9af5e8425c8f5a3"
mediastack_url = "http://api.mediastack.com/v1/news"

mediastack_params = {
    'access_key': MEDIASTACK_API_KEY,
    'keywords': 'AAPL',
    'languages': 'en',
    'limit': 5,
    'sort': 'published_desc'
}

try:
    response = requests.get(mediastack_url, params=mediastack_params, timeout=10)
    
    # Check response
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('data', [])
        
        print(f"Success! Retrieved {len(articles)} articles")
        
        # Print first article title if available
        if articles:
            first_article = articles[0]
            title = first_article.get('title', 'No title')
            print(f"First article title: {title}")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Error: {str(e)}")

print("\nNow testing Currents API")
CURRENTS_API_KEY = "O5_JjrWdlLN2v93iuKbhEhA9OSIYfChf4Cx9XE9xXgW1oYTC"
currents_url = "https://api.currentsapi.services/v1/search"

currents_params = {
    'apiKey': CURRENTS_API_KEY,
    'keywords': 'AAPL',
    'language': 'en',
    'limit': 5
}

try:
    response = requests.get(currents_url, params=currents_params, timeout=10)
    
    # Check response
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('news', [])
        
        print(f"Success! Retrieved {len(articles)} articles")
        
        # Print first article title if available
        if articles:
            first_article = articles[0]
            title = first_article.get('title', 'No title')
            print(f"First article title: {title}")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Error: {str(e)}")

print("\nTests completed.") 