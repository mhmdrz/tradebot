import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fill_empty_times(events):
    mem = ''
    for x in events:
        if x['time'] == '':
            x['time'] = mem
        else:
            mem = x['time']
    return events

def extract_times(events):
    times = []
    for x in events:
        if 'red' in x['impact']:
            times.append(x['time'])
    times = list(set(times))
    times = list(filter(lambda x: any(strs in x for strs in ['am', 'pm']), times))
    return sorted([datetime.strptime(t, '%I:%M%p') for t in times])

def get_events(url, headers):
    response = requests.get(url, headers=headers)
    if response.status != 200:
        print("Error Getting Events!")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', attrs={'class': 'calendar__table'})
            
    events = []
    for row in table.find_all('tr', attrs={'class': 'calendar__row'}):
        tmp = {}
        cell = row.find('td', attrs={'class': 'calendar__impact'})
        tmp['impact'] = str(cell.span['class']) if cell else ''
        tmp['currency'] = row.find('td', attrs={'class': 'calendar__currency'}).text.strip() if cell else ''
        tmp['title'] = row.find('td', attrs={'class': 'calendar__event'}).text.strip() if cell else ''
        tmp['time'] = row.find('td', attrs={'class': 'calendar__time'}).text.strip() if cell else ''
        events.append(tmp)
    
    events = fill_empty_times(events)

    return extract_times(events)