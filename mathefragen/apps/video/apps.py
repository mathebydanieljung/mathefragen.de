from django.apps import AppConfig


class VideoConfig(AppConfig):
    name = 'mathefragen.apps.video'

    def ready(self):
        import mathefragen.apps.video.signals
