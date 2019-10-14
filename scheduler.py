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
    cmd = []
    subprocess.call()
    print()


if __name__ == '__main__':
    update()
    # scheduler = BlockingScheduler()
    # scheduler.add_job(tick, trigger='cron', hour=15, minute=31)
    # print('Press Ctrl+C to exit')
    # try:
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     pass
