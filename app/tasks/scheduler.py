from celery.schedules import crontab

from app.tasks import app

app.conf.beat_schedule = {
    'nightly-github-sync': dict(
        task='app.tasks.core.sync_adapter_task',
        schedule=crontab(hour=3, minute=0),
        args=("github", {"repo": "axios/axios"})),
}
