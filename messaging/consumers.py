import logging

from asgiref.sync import async_to_sync

from channels.exceptions import StopConsumer
from channels.generic.websocket import JsonWebsocketConsumer

from django.dispatch import receiver as signal_receiver

from stringcase import snakecase

from .models import Message, Presence, PresenceGroup
from .signals import presence_changed
from .utilities import sync_group_send

logger = logging.getLogger(__name__)


def current_presence(presence_group):
    return {
        presence.staff_key: {
            'status': 'active',
            'idleTime': presence.idle_seconds,
        }
        for presence in presence_group.get_active()
    }


@signal_receiver(presence_changed)
def broadcast_presence_cb(sender, presence_group, **kwargs):
    """
    Will be called when a PresenceGroup is joined or left.
    """
    if not presence_group.channel_name.startswith('organization'):
        return

    sync_group_send(presence_group.channel_name, {
        'type': 'messaging.presence',
        'presences': current_presence(presence_group)
    })


class MessagingJsonConsumer(JsonWebsocketConsumer):

    def sync_group_send(self, channel_name, message):
        async_to_sync(self.channel_layer.group_send)(channel_name, message)

    def add_group(self, group, account_key):
        PresenceGroup.objects.add(group, self.channel_name, account_key)

        if not hasattr(self, 'presence_groups'):
            self.presence_groups = []

        self.presence_groups.append(group)

    def send_account(self, account_key, message):
        self.sync_group_send(f'account.{account_key}', {
            'type': 'messaging.receive',
            'message': message,
        })

    def update_presence(self):
        Presence.objects.touch(self.channel_name)

    def receive_json(self, content):
        logger.info(f'{self.account_key}: received {content}')

        self.update_presence()

        if content == 'heartbeat' or 'type' not in content:
            return

        method_name = f"type_{snakecase(content['type'])}"

        logger.info(f'{self.account_key}: dispatching "{method_name}"')

        if hasattr(self, method_name):
            handler = getattr(self, method_name)
            handler(content)

    def websocket_disconnect(self, message):
        # logger.info(f'{self.account_key}: websocket_disconnect called\nmessage: {message}')

        # if hasattr(self, 'presence_groups'):
        #     for group in self.presence_groups:
        #         PresenceGroup.objects.remove(group, self.channel_name)

        raise StopConsumer()

    #
    # Channel layer handlers
    #

    def messaging_receive(self, content):
        self.send_json(content['message'])


class FrontendConsumer(MessagingJsonConsumer):

    def send_organization(self, message):
        self.sync_group_send(f'organization.{self.customer_identifier}', {
            'type': 'messaging.receive',
            'message': message,
        })

    @property
    def organization_group_name(self):
        return f'organization.{self.customer_identifier}'

    @property
    def organization_group(self):
        return PresenceGroup.objects.get(channel_name=self.organization_group_name)

    def save_account_details(self):
        customer_identifier = self.scope['user']['customer_identifier']
        account_key = self.scope['user']['staff_key']

        if not account_key or not customer_identifier:
            raise ValueError('account_key or customer_identifier was set incorrectly')

        self.customer_identifier = customer_identifier
        self.account_key = account_key

        self.add_group(f'account.{self.account_key}', self.account_key)
        self.add_group(self.organization_group_name, self.account_key)

    def connect(self):
        if not self.scope['user']:
            return self.close()

        self.save_account_details()

        self.accept()

    def create_message(self, content, receiver, sender=None):
        if not sender:
            sender = self.account_key

        message = Message(
            customer_identifier=self.customer_identifier,
            sender=sender,
            receiver=receiver,
            content=content)
        message.save()

        return message

    #
    # Front-end handlers
    #

    def type_send_message(self, content):
        message = self.create_message(content=content['content'], receiver=content['to'])

        # send it back to ourselves so we have the metadata about it
        self.send_account(self.account_key, {
            'type': 'receive-message',
            'key': content['to'],
            'message': message.wire_representation(),
        })

        # TODO update notifications here
        if not Presence.objects.is_active(self.organization_group_name, content['to']):
            logger.info(f'{self.account_key}: {content["to"]} is inactive')

        self.send_account(
            content['to'], {
                'type': 'receive-message',
                'key': self.account_key,
                'message': message.wire_representation(),
            })

    def type_receive_message(self, content):
        self.send_json(content)

    def type_join(self, content):
        self.update_presence()

        messages = reversed(Message.objects.by_conversation(self.account_key, content['key'])[:25])

        self.send_json({
            'type': 'backfill',
            'key': content['key'],
            'messages': [message.wire_representation() for message in messages],
        })

        self.send_json({
            'type': 'presence',
            'presences': current_presence(self.organization_group),
        })

    #
    # Channel layer handlers
    #

    def messaging_presence(self, content):
        self.send_json({
            'type': 'presence',
            'presences': content['presences'],
        })
