from datetime import datetime
currentYear = datetime.now().year


def year(request):
    return {
        'year': currentYear
    }
