import os
import json
import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from .models import OAuthState

# Установить OAUTHLIB_INSECURE_TRANSPORT для разработки
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

CLIENT_SECRET_FILE = settings.CLIENT_SECRET_FILE
SCOPES = settings.SCOPES
REDIRECT_URI = settings.REDIRECT_URI

def index(request):
    return render(request, 'calculator/index.html')

def calculate(request):
    if request.method == 'POST':
        participants = int(request.POST['participants'])
        salary = float(request.POST['salary'])
        duration = float(request.POST['duration'])

        hourly_rate = salary / 176  # Предполагаем 176 рабочих часов в месяц
        cost = participants * hourly_rate * (duration / 60)

        return JsonResponse({'cost': cost})

def google_login(request):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    print('!!!!!!', authorization_url)

    # Сохранение состояния в базе данных
    OAuthState.objects.create(state=state)

    request.session['state'] = state
    print("Saved state:", state)
    print("Session data:", request.session.items())

    return redirect(authorization_url)


def oauth2callback(request):
    state_from_url = request.GET.get('state', None)
    print("Loaded state from URL:", state_from_url)

    try:
        oauth_state = OAuthState.objects.get(state=state_from_url)
        state = oauth_state.state
    except OAuthState.DoesNotExist:
        state = None

    print("Loaded state from DB:", state)
    if not state:
        return HttpResponseBadRequest('Session state not found')

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI

    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    return redirect('calendar')

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def calendar(request):
    creds = None
    if 'credentials' in request.session:
        creds = Credentials(**request.session['credentials'])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return redirect('google_login')

    service = build("calendar", "v3", credentials=creds)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    events_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'No Title')
        events_list.append({'start': start, 'summary': summary})

    return render(request, 'calculator/calendar.html', {'events': events_list})
