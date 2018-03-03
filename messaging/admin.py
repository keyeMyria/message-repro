import arrow

from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    def formatted_time(self, obj):
        return arrow.get(obj.timestamp).to('US/Pacific').format('YY/MM/DD HH:mm:ss')

    formatted_time.short_description = 'Time (Pacific)'
    formatted_time.admin_order_field = 'message_time'

    date_hierarchy = 'timestamp'

    list_display = (
        'id',
        'formatted_time',
        'customer_identifier',
        'sender',
        'receiver',
        'content',
    )

    list_filter = ('customer_identifier',)

    readonly_fields = (
        'id',
        'customer_identifier',
        'conversation_key',
        'timestamp',
        'sender',
        'receiver',
        'content',
    )

    search_fields = (
        'content',
        'sender',
        'receiver',
    )


admin.site.site_title = 'Messaging administration'
admin.site.site_header = 'Messaging administration'
