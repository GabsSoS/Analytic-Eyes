from django.contrib import admin
from .models import Pipeline, PipelineRun, PipelinePermission

admin.site.register(Pipeline)
admin.site.register(PipelineRun)
admin.site.register(PipelinePermission)