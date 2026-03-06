from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pipelines", "0002_pipeline_container_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="script_path",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
