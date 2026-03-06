from celery import shared_task
from pathlib import Path
import os
import posixpath

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from docker import from_env as docker_from_env
from docker.errors import DockerException

from .models import PipelineRun


def _resolve_script_paths(script_path):
    normalized = script_path.strip().replace("\\", "/").lstrip("/")
    if not normalized:
        raise ValueError("Pipeline script_path is required")

    relative_script = Path(normalized)
    if relative_script.is_absolute() or ".." in relative_script.parts:
        raise ValueError("Invalid script_path")

    scripts_dir = Path(settings.PIPELINE_SCRIPTS_DIR).resolve()
    host_script = (scripts_dir / relative_script).resolve()
    if not host_script.is_file() or scripts_dir not in host_script.parents:
        raise FileNotFoundError(f"Script not found: {normalized}")

    return scripts_dir, normalized


@shared_task
def execute_pipeline(run_id):
    container = None
    log_lines = []

    with transaction.atomic():
        run = (
            PipelineRun.objects
            .select_for_update()
            .select_related("pipeline")
            .get(id=run_id)
        )

        if run.status in (PipelineRun.Status.SUCCESS, PipelineRun.Status.FAILED):
            return

        run.status = PipelineRun.Status.RUNNING
        run.started_at = run.started_at or timezone.now()
        run.save(update_fields=["status", "started_at"])

    try:
        pipeline = run.pipeline
        scripts_dir, normalized_script_path = _resolve_script_paths(pipeline.script_path)

        running_inside_docker = Path("/.dockerenv").exists() and bool(os.getenv("HOSTNAME"))
        if running_inside_docker:
            script_in_container = posixpath.join("/app/pipeline_scripts", normalized_script_path)
            run_kwargs = {
                "volumes_from": [f"{os.getenv('HOSTNAME')}:ro"],
            }
        else:
            script_in_container = posixpath.join("/opt/pipeline_scripts", normalized_script_path)
            run_kwargs = {
                "volumes": {
                    str(scripts_dir): {
                        "bind": "/opt/pipeline_scripts",
                        "mode": "ro",
                    }
                },
            }

        image = pipeline.container_image
        command_template = pipeline.container_command.strip()
        if command_template:
            command = command_template.replace("{script_path}", script_in_container)
        else:
            command = f"python {script_in_container}"

        environment = {
            **pipeline.container_env,
            "PIPELINE_ID": str(pipeline.id),
            "PIPELINE_RUN_ID": str(run.id),
            "PIPELINE_SCRIPT_PATH": script_in_container,
        }

        client = docker_from_env()
        container_name = f"etl-run-{run.id}"

        container = client.containers.run(
            image=image,
            command=command,
            name=container_name,
            environment=environment,
            detach=True,
            labels={
                "app": "analytic-eyes",
                "pipeline_id": str(pipeline.id),
                "pipeline_run_id": str(run.id),
            },
            **run_kwargs,
        )

        for raw_line in container.logs(stream=True, follow=True):
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            if line:
                log_lines.append(line)

        result = container.wait(timeout=pipeline.container_timeout_seconds)
        exit_code = result.get("StatusCode", 1)

        run.status = (
            PipelineRun.Status.SUCCESS
            if exit_code == 0
            else PipelineRun.Status.FAILED
        )

        if exit_code != 0:
            log_lines.append(f"Container finished with exit code {exit_code}")

    except DockerException as exc:
        run.status = PipelineRun.Status.FAILED
        log_lines.append(f"Docker error: {exc}")
    except Exception as exc:
        run.status = PipelineRun.Status.FAILED
        log_lines.append(f"Unexpected error: {exc}")
    finally:
        run.finished_at = timezone.now()
        run.log = "\n".join(log_lines)[-50000:]
        run.save(update_fields=["status", "finished_at", "log"])

        if container is not None:
            try:
                container.remove(force=True)
            except DockerException:
                # No-op: execution result is already persisted.
                pass
