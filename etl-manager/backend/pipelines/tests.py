from django.contrib.auth.models import User
from django.test import TestCase

from .models import Pipeline


class PipelineAnchorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            password="123456",
        )
        self.pipeline_a = Pipeline.objects.create(
            name="Pipeline A",
            description="",
            etl_name="etls/pipeline_a",
            owner=self.user,
        )
        self.pipeline_b = Pipeline.objects.create(
            name="Pipeline B",
            description="",
            etl_name="etls/pipeline_b",
            owner=self.user,
        )
        self.pipeline_c = Pipeline.objects.create(
            name="Pipeline C",
            description="",
            etl_name="etls/pipeline_c",
            owner=self.user,
        )

    def test_set_trigger_sources_accepts_valid_chain(self):
        self.pipeline_b.set_trigger_sources([self.pipeline_a])
        self.pipeline_c.set_trigger_sources([self.pipeline_b])

        self.assertQuerySetEqual(
            self.pipeline_b.trigger_targets.order_by("id"),
            [self.pipeline_a],
            transform=lambda pipeline: pipeline,
        )
        self.assertQuerySetEqual(
            self.pipeline_a.trigger_sources.order_by("id"),
            [self.pipeline_b],
            transform=lambda pipeline: pipeline,
        )

    def test_set_trigger_sources_rejects_cycle(self):
        self.pipeline_b.set_trigger_sources([self.pipeline_a])
        self.pipeline_c.set_trigger_sources([self.pipeline_b])

        with self.assertRaisesMessage(ValueError, "ciclo"):
            self.pipeline_a.set_trigger_sources([self.pipeline_c])

    def test_set_trigger_sources_rejects_self_reference(self):
        with self.assertRaisesMessage(ValueError, "nela mesma"):
            self.pipeline_a.set_trigger_sources([self.pipeline_a])
