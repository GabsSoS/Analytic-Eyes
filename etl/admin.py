from django.contrib import admin
from etl.models import ETL
# Register your models here.
@admin.register(ETL)
class ETLsAdmin(admin.ModelAdmin):
    list_display = ('owner', 'title')