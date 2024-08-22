from django.apps import AppConfig


class QuestionConfig(AppConfig):
    name = 'mathefragen.apps.question'

    def ready(self):
        import mathefragen.apps.question.signals
