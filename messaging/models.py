from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils.timezone import now

from .signals import presence_changed
from .utilities import sync_group_add, sync_group_discard


def get_conversation_key(*participants):
    return '/'.join(sorted(participants))


class MessageQuerySet(models.QuerySet):

    def by_conversation(self, *participants):
        return self.filter(conversation_key=get_conversation_key(*participants))


class Message(models.Model):

    objects = MessageQuerySet.as_manager()

    class Meta:
        ordering = ['-timestamp']

    customer_identifier = models.CharField(max_length=32)

    # TODO add customer_identifier to conversation_key?
    conversation_key = models.CharField(max_length=65, editable=False, db_index=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    sender = models.CharField(max_length=32)
    receiver = models.CharField(max_length=32)

    content = models.TextField()

    def wire_representation(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'conversationKey': self.conversation_key,
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
        }

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        self.conversation_key = get_conversation_key(self.sender, self.receiver)

        super().save(*args, **kwargs)


class PresenceManager(models.Manager):

    def touch(self, channel_name):
        self.filter(channel_name=channel_name).update(last_seen=now())

    def leave_all(self, channel_name):
        for presence in self.select_related('presence_group').filter(channel_name=channel_name):
            presence_group = presence.presence_group
            presence_group.remove_presence(presence=presence)

    def is_active(self, channel_name, staff_key):
        expired_at = now() - timedelta(seconds=settings.PRESENCE_MAX_AGE_IN_SECONDS)

        return (self.filter(last_seen__gt=expired_at,
                            presence_group__channel_name=channel_name,
                            staff_key=staff_key).count()) > 0  # yapf: disable


class Presence(models.Model):

    class Meta:
        unique_together = [('presence_group', 'channel_name')]

    presence_group = models.ForeignKey('PresenceGroup', on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=255, help_text='Reply channel for the connection')
    staff_key = models.CharField(max_length=32)
    last_seen = models.DateTimeField(default=now)

    @property
    def idle_seconds(self):
        return (now() - self.last_seen).total_seconds()

    objects = PresenceManager()

    def __str__(self):
        return f'{self.presence_group}: {self.staff_key} {self.last_seen}'


class PresenceGroupManager(models.Manager):

    def add(self, presence_group_channel_name, user_channel_name, staff_key):
        presence_group, _ = self.get_or_create(channel_name=presence_group_channel_name)
        presence_group.add_presence(user_channel_name, staff_key)

        return presence_group

    def remove(self, presence_group_channel_name, user_channel_name):
        try:
            presence_group = self.get(channel_name=presence_group_channel_name)
        except PresenceGroup.DoesNotExist:
            return

        presence_group.remove_presence(user_channel_name)

    def prune_presences(self, age=None):
        pruned_count = 0

        for presence_group in self.all():
            pruned_count += presence_group.prune_presences(age)

        return pruned_count

    def prune_presence_groups(self):
        self.filter(presence__isnull=True).delete()


class PresenceGroup(models.Model):

    channel_name = models.CharField(
        max_length=255, unique=True, help_text='Group channel name for this presence group')

    objects = PresenceGroupManager()

    def __str__(self):
        return self.channel_name

    def add_presence(self, channel_name, staff_key):
        presence, created = (Presence.objects
                             .get_or_create(presence_group=self,
                                            channel_name=channel_name,
                                            staff_key=staff_key))  # yapf: disable

        if created:
            sync_group_add(self.channel_name, channel_name)

            self.broadcast_changed(added=presence)

    def remove_presence(self, channel_name=None, presence=None):
        if presence is None:
            try:
                presence = Presence.objects.get(presence_group=self, channel_name=channel_name)
            except Presence.DoesNotExist:
                return

        sync_group_discard(self.channel_name, presence.channel_name)

        presence.delete()

        self.broadcast_changed(removed=presence)

    def prune_presences(self, age_in_seconds=None):
        if not age_in_seconds:
            age_in_seconds = settings.PRESENCE_MAX_AGE_IN_SECONDS

        num_deleted, _ = (Presence.objects
                          .filter(presence_group=self,
                                  last_seen__lt=now() - timedelta(seconds=age_in_seconds))
                          .delete())  # yapf: disable

        if num_deleted > 0:
            self.broadcast_changed(bulk_change=True)

        return num_deleted or 0

    def get_active(self):
        return list(
            Presence.objects
            .filter(
                presence_group=self,
                last_seen__gte=now() - timedelta(seconds=settings.PRESENCE_MAX_AGE_IN_SECONDS))
            .distinct())  # yapf: disable

    def broadcast_changed(self, added=None, removed=None, bulk_change=False):
        presence_changed.send(
            sender=self.__class__,
            presence_group=self,
            added=added,
            removed=removed,
            bulk_change=bulk_change)
