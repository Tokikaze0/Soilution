# yourapp/context_processors.py

from .models import Message

def recent_messages(request):
    if request.user.is_authenticated:
        messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:5]
        return {'recent_messages': messages}
    return {}
