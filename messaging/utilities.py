from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

sync_group_add = async_to_sync(channel_layer.group_add)
sync_group_discard = async_to_sync(channel_layer.group_discard)

sync_group_send = async_to_sync(channel_layer.group_send)
