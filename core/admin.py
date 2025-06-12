from django.contrib import admin
from .models import Event

class EventAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/admin.css',)  # Path relative to /static/
        }

    list_display = ('name', 'date', 'location', 'description')
    search_fields = ('name', 'location')
    list_filter = ('date',)
    ordering = ('-date',)
    fields = ('name', 'date', 'location', 'description')
    list_per_page = 20

admin.site.register(Event, EventAdmin)
