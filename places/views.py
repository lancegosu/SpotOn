import requests
from django.shortcuts import render
from .forms import PlaceSearchForm
from django.http import JsonResponse
from django.conf import settings

# Create views here.

# View for searching places using the Google Places API
def search_places(request):
    gmaps_api_key = settings.GMAPS_API_KEY
    results = []

    if request.method == 'POST':
        # Process the search form if it's a POST request
        form = PlaceSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']

            # Make a request to the Google Places API
            base_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
            params = {
                'query': query,
                'key': gmaps_api_key,
            }
            response = requests.get(base_url, params=params)
            data = response.json()

            # Process the API response and extract relevant information
            if 'results' in data:
                results = [
                    {
                        'name': place['name'],
                        'address': place.get('formatted_address', 'N/A'),
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng'],
                        'place_id': place['place_id'],
                        'details': {
                            'business_status': place.get('business_status', 'N/A'),
                            'price_level': place.get('price_level', 'N/A'),
                            'rating': place.get('rating', 'N/A'),
                            'types': place.get('types', []),
                            'user_ratings_total': place.get('user_ratings_total', 'N/A'),
                            # Add more details as needed
                        },
                    }
                    for place in data['results']
                ]

    else:
        form = PlaceSearchForm()

    return render(request, 'search.html', {'form': form, 'results': results, 'api_key': gmaps_api_key})

# Function to get reviews from the Google Places API (Place Details)
def get_reviews_from_api(place_id):
    # Make a request to the Google Places API (Place Details) to fetch reviews
    gmaps_api_key = settings.GMAPS_API_KEY
    details_url = 'https://maps.googleapis.com/maps/api/place/details/json'
    details_params = {
        'place_id': place_id,
        'key': gmaps_api_key,
        'fields': 'reviews',
    }
    response = requests.get(details_url, params=details_params)
    details_data = response.json()

    return details_data.get('result', {}).get('reviews', []) # Extract and return reviews

# View for handling questions and generating answers using ChatGPT
def ask_question(request):
    if request.method == 'POST':
        # Get information from the POST request
        place_name = request.POST.get('place_name')
        place_address = request.POST.get('place_address')
        question = request.POST.get('question')
        place_id = request.POST.get('place_id')
        
        reviews = get_reviews_from_api(place_id) # Fetch reviews for the selected place
        reviews_text = "".join([review['text'] for review in reviews]) # Join all the review texts into one string
        prompt = f"Use the reviews: {reviews_text}, from {place_name} at {place_address}, to answer the given query: {question}." # Construct the prompt for ChatGPT

        # Make a request to the ChatGPT API
        openai_api_key = settings.OPENAI_API_KEY
        openai_api_url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {openai_api_key}',
        }
        data = {
            'model': 'gpt-3.5-turbo-1106',  # Specify the GPT model name
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt},
            ],
        }

        # Send the request and extract the answer from ChatGPT's response
        response = requests.post(openai_api_url, json=data, headers=headers)
        data = response.json()
        answer = data['choices'][0]['message']['content']
        return JsonResponse({'answer': answer})
        
    else:
        return render(request, '404.html')  # Handle GET requests appropriately
