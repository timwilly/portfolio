from app import scheduler
from app.tasks import import_data_business_montreal
from pytz import timezone


eastern_tz = timezone('US/Eastern')

@scheduler.task('cron', id='schedule import business montreal', 
                hour=0, minute=0, second=0, misfire_grace_time=1000, 
                timezone=eastern_tz)
def schedule_import_business_montreal():
    with scheduler.app.app_context():
        import_data_business_montreal()