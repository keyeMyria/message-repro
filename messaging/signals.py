from django import dispatch

presence_changed = dispatch.Signal(
    providing_args=['presence_group', 'added', 'removed', 'bulk_change'])
