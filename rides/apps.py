from django.apps import AppConfig



class RidesConfig(AppConfig):
    name = 'rides'

    def ready(self):
        import rides.signals