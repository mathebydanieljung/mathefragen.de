from django.contrib import admin

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

        message_obj.save()
