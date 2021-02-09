from django.contrib import admin
from .models import (
    Talk,
    Workshop,
    Presenter,
    EventService,
)


admin.site.register(Talk)
admin.site.register(Workshop)
admin.site.register(EventService)
admin.site.register(Presenter)

