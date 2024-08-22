from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'mathefragen.apps.user'

    def ready(self):
        import mathefragen.apps.user.signals
