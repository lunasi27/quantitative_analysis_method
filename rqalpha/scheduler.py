from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import subprocess

ENV = {
    'path': '/usr/local/bin',
}


def update():
    cmd = ['rqalpha', 'update-bundle']
    subprocess.call(cmd)
    print('Tick! The time is: %s' % datetime.now())


def exec_select():
    update()
    # rqalpha run -f main.py -s 2019-10-14
    cmd = ['rqalpha', 'run', '-f', 'main.py', '-s', '%s' % datetime.now().date()]
    subprocess.call(cmd)
    print('Calculate new selected stocks.')


if __name__ == '__main__':
    # update()
    # exec_select()
    scheduler = BlockingScheduler()
    scheduler.add_job(exec_select, trigger='cron', hour=21)
    print('Press Ctrl+C to exit')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
