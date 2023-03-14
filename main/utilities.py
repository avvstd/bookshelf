from django.template.loader import render_to_string
from django.core.signing import Signer
from django.utils.encoding import smart_str
from datetime import datetime, date
from os.path import splitext

from bookshelf.settings import ALLOWED_HOSTS

signer = Signer()

def get_activation_host():
    if ALLOWED_HOSTS:
        first_host = ALLOWED_HOSTS[0]
        if 'localhost' in first_host and not 'localhost:' in first_host:
            host = first_host + ':8000'
        else:
            host = 'http://' + first_host
    else:
        host = 'http://localhost:8000'

    return host

def send_activation_notification(user):
    host = get_activation_host()

    context = {
        'user': user,
        'host': host,
        'sign': signer.sign(user.username)
    }
    
    subject = render_to_string('email/activation_letter_subject.txt', context)
    body = render_to_string('email/activation_letter_body.txt', context)

    user.email_user(subject, body)

def get_upload_path(instance, filename):
    # Migration problem.
    return get_userpics_upload_path(instance, filename)

def get_userpics_upload_path(instance, filename):
    return 'userpics/%s%s' % (datetime.now().timestamp(), splitext(filename)[1])

def get_covers_upload_path(instance, filename):
    return 'covers/%s%s' % (datetime.now().timestamp(), splitext(filename)[1])

def handle_shelf_file(f):

    data = []

    for line in f:
        encoded_line = smart_str(line, encoding='utf-8')
        try:
            parsed_data = parsed_line(encoded_line)
        except:
            raise Exception('Parsing error')
        
        data.append(parsed_data)

    return data        

def parsed_line(line):
    
    result = {}

    #Date
    ind = line.rfind('"')
    rem = line[:ind]
    ind = rem.rfind('"')
    raw_date = rem[ind+1:].strip()
    result['read_date'] = parsed_read_date(raw_date)

    #Rating
    rem = rem[:ind-1]
    ind = rem.rfind(',')
    raw_rating = rem[ind+1:].strip()
    result['rating'] = len(raw_rating)

    #Author
    rem = rem[:ind]
    ind = rem.rfind(',')
    rem = rem[:ind]
    ind = rem.rfind(',')
    result['author'] = rem[ind+1:].strip()

    #Title
    raw_title = rem[:ind].strip()
    if raw_title[len(raw_title)-1] == '"':
        raw_title = raw_title[:len(raw_title)-1]
    if raw_title[0] == '"':
        raw_title = raw_title[1:]
    result['title'] = raw_title.strip()

    return result

def parsed_read_date(raw_date):
    ind = raw_date.find(',')
    day_and_month = raw_date[:ind]
    year = raw_date[ind+2:ind+6]
    ind = day_and_month.find(' ')
    month = day_and_month[:ind].strip()
    day = day_and_month[ind+1:].strip()

    year_numeric = int(year)
    if month == 'January':
        month_numeric = 1
    elif month == 'February':
        month_numeric = 2
    elif month == 'March':
        month_numeric = 3
    elif month == 'April':
        month_numeric = 4
    elif month == 'May':
        month_numeric = 5
    elif month == 'June':
        month_numeric = 6
    elif month == 'July':
        month_numeric = 7
    elif month == 'August':
        month_numeric = 8
    elif month == 'September':
        month_numeric = 9
    elif month == 'October':
        month_numeric = 10
    elif month == 'November':
        month_numeric = 11
    elif month == 'December':
        month_numeric = 12
    else:
        raise Exception('Month parsing error')

    day_numeric = int(day)
    return date(year_numeric, month_numeric, day_numeric)