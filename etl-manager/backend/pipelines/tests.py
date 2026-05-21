from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import Pipeline, PipelineSchedule
from .tasks import dispatch_due_schedules


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


class PipelineScheduleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="scheduler",
            password="123456",
        )
        self.pipeline = Pipeline.objects.create(
            name="Pipeline Schedule",
            description="",
            etl_name="etls/pipeline_schedule",
            owner=self.user,
        )

    def test_compute_next_run_at_uses_next_matching_weekday(self):
        reference_time = datetime(2026, 5, 18, 10, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))

        next_run_at = PipelineSchedule.compute_next_run_at(
            days_of_week=[0, 2],
            hour=11,
            minute=15,
            timezone_name="America/Sao_Paulo",
            reference_time=reference_time,
        )

        next_run_local = timezone.localtime(next_run_at, ZoneInfo("America/Sao_Paulo"))
        self.assertEqual(next_run_local.weekday(), 0)
        self.assertEqual(next_run_local.hour, 11)
        self.assertEqual(next_run_local.minute, 15)
        self.assertEqual(next_run_local.date().isoformat(), "2026-05-18")

    def test_compute_next_run_at_rolls_to_next_available_day(self):
        reference_time = datetime(2026, 5, 18, 11, 30, tzinfo=ZoneInfo("America/Sao_Paulo"))

        next_run_at = PipelineSchedule.compute_next_run_at(
            days_of_week=[0, 2],
            hour=11,
            minute=15,
            timezone_name="America/Sao_Paulo",
            reference_time=reference_time,
        )

        next_run_local = timezone.localtime(next_run_at, ZoneInfo("America/Sao_Paulo"))
        self.assertEqual(next_run_local.weekday(), 2)
        self.assertEqual(next_run_local.date().isoformat(), "2026-05-20")

    @patch("pipelines.tasks.queue_pipeline_execution")
    @patch("pipelines.tasks.redis.from_url")
    def test_dispatch_due_schedules_advances_next_run_and_queues_pipeline(
        self,
        redis_from_url_mock,
        queue_pipeline_execution_mock,
    ):
        fake_lock = redis_from_url_mock.return_value.lock.return_value
        fake_lock.acquire.return_value = True

        now = timezone.now()
        schedule = PipelineSchedule.objects.create(
            pipeline=self.pipeline,
            enabled=True,
            days_of_week=[now.weekday()],
            hour=(now.hour + 23) % 24,
            minute=now.minute,
            timezone_name="America/Sao_Paulo",
            created_by=self.user,
        )
        PipelineSchedule.objects.filter(id=schedule.id).update(
            next_run_at=now - timedelta(minutes=1)
        )

        dispatched_count = dispatch_due_schedules()

        schedule.refresh_from_db()
        self.assertEqual(dispatched_count, 1)
        queue_pipeline_execution_mock.assert_called_once_with(self.pipeline, self.user)
        self.assertIsNotNone(schedule.last_triggered_at)
        self.assertIsNotNone(schedule.next_run_at)
        self.assertGreater(schedule.next_run_at, now)
