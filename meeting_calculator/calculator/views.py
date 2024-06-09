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

# OAUTHLIB_INSECURE_TRANSPORT для разработки
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

    return redirect('calendar_list')

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def calendar_list(request):
    creds = None
    if 'credentials' in request.session:
        creds = Credentials(**request.session['credentials'])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return redirect('google_login')

    service = build("calendar", "v3", credentials=creds)
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])

    calendar_choices = [(calendar['id'], calendar['summary']) for calendar in calendars]

    return render(request, 'calculator/calendar_list.html', {'calendar_choices': calendar_choices})



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

    calendar_id = request.GET.get('calendar_id', 'primary')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    salary = float(request.GET.get('salary', 0))

    # Проверка на отрицательную зарплату
    if salary < 0:
        return render(request, 'calculator/calendar.html', {
            'events': [],
            'total_time': '0 minutes',
            'total_cost': '$0.00',
            'start_date': start_date,
            'end_date': end_date,
            'error': 'Salary cannot be negative.'
        })

    if start_date and end_date:
        time_min = datetime.datetime.strptime(start_date, '%Y-%m-%d').isoformat() + 'Z'
        time_max = datetime.datetime.strptime(end_date, '%Y-%m-%d').isoformat() + 'Z'
    else:
        time_min = datetime.datetime.utcnow().isoformat() + 'Z'
        time_max = None

    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min,
                                          timeMax=time_max, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    events_list = []
    total_duration = 0

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        summary = event.get('summary', 'No Title')

        start_time = datetime.datetime.fromisoformat(start)
        end_time = datetime.datetime.fromisoformat(end)
        duration = (end_time - start_time).total_seconds() / 60  # Продолжительность в минутах

        # Отфильтровываем события, которые больше 8 часов (480 минут)
        if duration <= 480:
            total_duration += duration
            formatted_start = start_time.strftime('%Y-%m-%d')
            formatted_duration = f"{int(duration // 60)} hours {int(duration % 60)} minutes" if duration >= 60 else f"{int(duration)} minutes"
            events_list.append({'start': formatted_start, 'summary': summary, 'duration': formatted_duration})

    participants = 1
    hourly_rate = salary / 176
    total_cost = participants * hourly_rate * (total_duration / 60)

    total_hours = int(total_duration // 60)
    total_minutes = int(total_duration % 60)
    total_time_formatted = f'{total_hours} hours {total_minutes} minutes'

    return render(request, 'calculator/calendar.html', {
        'events': events_list,
        'total_time': total_time_formatted,
        'total_cost': f'${total_cost:.2f}',
        'start_date': start_date,
        'end_date': end_date
    })