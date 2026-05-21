from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pipelines", "0003_pipeline_trigger_sources"),
    ]

    operations = [
        migrations.CreateModel(
            name="PipelineSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=False)),
                ("days_of_week", models.JSONField(blank=True, default=list)),
                ("hour", models.PositiveSmallIntegerField(default=0)),
                ("minute", models.PositiveSmallIntegerField(default=0)),
                ("timezone_name", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("next_run_at", models.DateTimeField(blank=True, null=True)),
                ("last_triggered_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_pipeline_schedules",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "pipeline",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedule",
                        to="pipelines.pipeline",
                    ),
                ),
            ],
            options={
                "ordering": ("pipeline_id",),
            },
        ),
    ]
