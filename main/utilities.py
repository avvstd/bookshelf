from django.template.loader import render_to_string
from django.core.signing import Signer
from datetime import datetime
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