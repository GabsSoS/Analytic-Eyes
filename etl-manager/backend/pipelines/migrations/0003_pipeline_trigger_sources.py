from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pipelines", "0002_pipeline_etl_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="trigger_sources",
            field=models.ManyToManyField(
                blank=True,
                related_name="trigger_targets",
                symmetrical=False,
                to="pipelines.pipeline",
            ),
        ),
    ]
