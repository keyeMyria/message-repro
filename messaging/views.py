from django.db.models import Q

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Message


def not_me(message, staff_key):
    return message.sender if message.sender != staff_key else message.receiver


def recent_messages(customer_identifier, staff_key):
    messages = (Message.objects
                .filter(customer_identifier=customer_identifier)
                .filter(Q(sender=staff_key) |
                        Q(receiver=staff_key))
                .order_by('conversation_key', '-timestamp')
                .distinct('conversation_key'))  # yapf: disable

    return {
        not_me(message, staff_key): {
            'message': message.content,
            'timestamp': message.timestamp,
            'sender': message.sender,
        }
        for message in messages
    }


class MostRecentMessageTimes(APIView):

    @staticmethod
    def get(request):
        return Response(
            data=recent_messages(request.user.customer_identifier, request.user.staff_key))
