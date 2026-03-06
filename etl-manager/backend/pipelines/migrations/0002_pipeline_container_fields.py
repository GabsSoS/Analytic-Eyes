from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pipelines", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="container_command",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="container_env",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="container_image",
            field=models.CharField(default="python:3.11-slim", max_length=255),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="container_timeout_seconds",
            field=models.PositiveIntegerField(default=3600),
        ),
    ]
