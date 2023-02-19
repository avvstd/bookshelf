from django.shortcuts import render
from datetime import datetime

def index(request):
    ''' Main page. '''
    current_year = datetime.now().year
    context = {
        'year': current_year,
    }
    return render(request, 'main/index.html', context)
