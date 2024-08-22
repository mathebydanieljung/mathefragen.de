from django.conf import settings
from django.contrib import admin
from websocket import create_connection

from mathefragen.apps.messaging.models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    exclude = ('link', 'from_user', 'to_all')
    list_display = ('title', 'message', 'type', 'idate')
    filter_horizontal = ('to_users',)

    def save_related(self, request, form, formsets, change):
        super(MessageAdmin, self).save_related(request, form, formsets, change)
        message_obj = form.instance

        if not message_obj.type:
            message_obj.type = 'Mitteilung'

        if settings.ENABLE_WEBSOCKETS:
            for receiver in message_obj.to_users.all():
                try:
                    ws = create_connection(settings.WEBSOCKET_USER_PUSH_DOMAIN % receiver.id)
                    ws.send('new_comment')
                    ws.close()
                except Exception:
                    continue

            if not message_obj.to_users.count():
                message_obj.to_all = True
                try:
                    ws = create_connection(settings.WEBSOCKET_GLOBAL_PUSH_DOMAIN)
                    ws.close()
                except Exception:
                    pass

        message_obj.save()
