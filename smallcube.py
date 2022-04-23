#!/usr/bin/env python3
import logging
import sys
import time
import os
import sqlite3
import threading
import schedule
import uuid
import json
import socket
from collections import deque
import subprocess
from utils import *
from pydoc import locate
import RPi.GPIO as GPIO


class SmallCube:

    def __init__(self):
        self.dbname = 'db.sql'
        if not os.path.exists(self.dbname):
            InitDB(self.dbname)

        self.id_device = db_get_parm_conf(self.dbname, "MAIN", "id_device")
        self.size_deamon_queue = db_get_parm_conf(self.dbname, "MAIN", "size_daemon_queue")
        self.socketfile = "smallcube.sock"
        self.connectionTimeout = db_get_parm_conf(self.dbname, "PI_TALK", "connection_timeout")

        self.PCQ = PiCronQueue(int(self.size_deamon_queue))
        self.PDQ = PiDeamonQueue(int(self.size_deamon_queue))

        self.P = Plugins(self.dbname)

    def start(self):
        while True:
            try:
                if PD.is_alive() is False:
                    PD = PiDeamon(self.PCQ, self.PDQ, self.P, self.dbname)
                    PD.start()
            except Exception as e:
                print(e)
                PD = PiDeamon(self.PCQ, self.PDQ, self.P, self.dbname)
                PD.start()
            time.sleep(1)
            try:
                if PC.is_alive() is False:
                    PC = PiCron(self.PCQ, self.PDQ, self.P, self.dbname)
                    PC.start()
            except Exception as e:
                PC = PiCron(self.PCQ, self.PDQ, self.P, self.dbname)
                PC.start()
            time.sleep(1)
            try:
                if PT.is_alive() is False:
                    PT = PiTalk(self.PCQ, self.PDQ, self.socketfile, self.connectionTimeout, self.id_device)
                    PT.start()
            except Exception as e:
                PT = PiTalk(self.PCQ, self.PDQ, self.socketfile, self.connectionTimeout, self.id_device)
                PT.start()

            time.sleep(10)


class InitDB:
    def __init__(self, dbname):
        logging.info(f"InitDB: initiate {dbname}")
        conn = create_connection(dbname)
        self.c = conn.cursor()
        self.create_db()
        self.save_first_run()
        conn.commit()
        conn.close()

    def create_db(self):
        self.c.execute(
            '''CREATE TABLE conf (id integer primary key AUTOINCREMENT, module_name text, name text, value text)''')
        self.c.execute(
            '''CREATE TABLE picron (id integer primary key AUTOINCREMENT, name text, schedule_name text, schedule_parm text, module_name text, module_parms text, enabled integer)''')
        self.c.execute(
            '''CREATE TABLE gpio (id integer primary key AUTOINCREMENT, name text, pin_number integer, pin_conf text, pin_status text, enabled integer, reserved integer)''')
        self.c.execute(
            '''CREATE TABLE plugins (id integer primary key AUTOINCREMENT, plugin_name text, name text, value text)''')
        self.c.execute(
            '''CREATE TABLE plugins_data (id integer primary key AUTOINCREMENT, plugin_name text, name text, data text)''')

    def save_first_run(self):
        si = {'first_run_time': time.time(), 'id': uuid.uuid4(), 'user': pass_gen(10, 3), 'password': pin_gen(4)}
        with open('conn_app.txt', 'w') as file:
            file.write(f'ip: {get_ip()}\n')
            file.write(f'id: {si["id"]}\n')
            file.write(f'user: {si["user"]}\n')
            file.write(f'password: {si["password"]}\n')

        logging.info(f"InitDB: id device: {si['id']}")
        logging.info(f"InitDB: user: {si['user']}")
        logging.info(f"InitDB: password: {si['password']}")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'first_run', '{si['first_run_time']}')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'id_device', '{si['id']}')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'name', '')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'user', '{si['user']}')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'pass', '{si['password']}')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'app_connected', 'no')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'wait_for_ntp_sync', 'yes')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'MAIN', 'size_daemon_queue', '100')")

        self.c.execute(f"INSERT INTO conf VALUES (null, 'PI_TALK', 'connection_timeout', '5')")

        self.c.execute(f"INSERT INTO conf VALUES (null, 'GPIO', 'status', 'off')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'GPIO', 'gpio_setwarnings', 'False')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'GPIO', 'gpio_setmode', 'board')")

        self.c.execute(f"INSERT INTO conf VALUES (null, 'SCRIPT', 'status', 'off')")
        self.c.execute(f"INSERT INTO conf VALUES (null, 'PLUGIN', 'status', 'off')")

        gpio_number_on_board = 50
        for i in range(1, (gpio_number_on_board + 1)):
            self.c.execute("INSERT INTO gpio VALUES (null, 'Example name', ?, '', '',0,0)", (i,))


class PiTalk(threading.Thread):

    def __init__(self, PCQ, PDQ, socketfile, connectionTimeout, id_device):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.socketfile = socketfile
        self.connectionTimeout = connectionTimeout
        self.id_device = id_device
        self.PCQ = PCQ
        self.PDQ = PDQ
        if os.path.exists(self.socketfile):
            os.remove(self.socketfile)

    def run(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self.socketfile)
        s.listen(5)

        logging.info(f'PiTalk: server socket is ready and waiting for connections..')
        while True:
            client, ipPort = s.accept()
            client.settimeout(int(self.connectionTimeout))
            try:
                data = json.loads(client.recv(1024).decode())
                logging.info(f'PiTalk: received data: {data}')
                if data[0] == self.id_device:
                    try:
                        if data[1] == 'PICRON':
                            order = data[2]
                            self.PCQ.add(order)
                        elif data[1] == 'PIDEAMON':
                            order = data[2]
                            self.PDQ.add(order)
                    except Exception as e:
                        logging.warning(f'PiTalk: bad data, {e}')
                    else:
                        try:
                            client.send(json.dumps(['OK']).encode())
                        except Exception as e:
                            logging.warning(f'PiTalk: connection end without bye, exception: {e}')
                else:
                    logging.warning(f'PiTalk: bad id_device')
                    try:
                        client.send(json.dumps(['BADCOMMAND']).encode())
                    except Exception as e:
                        logging.warning(f'PiTalk: connection end without bye, {e}')
            except ValueError as e:
                logging.warning(f'PiTalk: received data is not json, {e}')
            except socket.timeout as e:
                logging.warning(f'PiTalk: connection timeout, {e}')
            finally:
                client.close()


class PiCronQueue:

    def __init__(self, size):
        self.cmd_queue = deque([])
        self.lock = threading.Lock()
        self.size = size

    def get(self):
        if len(self.cmd_queue) > 0:
            self.lock.acquire()
            try:
                order = self.cmd_queue.popleft()
            finally:
                self.lock.release()
            return order
        else:
            return None

    def add(self, order):
        if len(self.cmd_queue) < self.size:
            self.lock.acquire()
            try:
                self.cmd_queue.append(order)
            finally:
                self.lock.release()


# https://schedule.readthedocs.io/en/stable/api.html
class PiCron(threading.Thread):
    def __init__(self, PCQ, PDQ, P, dbname):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.PCQ = PCQ
        self.PDQ = PDQ
        self.LP = P
        self.dbname = dbname

    def setJobs(self):
        logging.info("PiCron: create new cron list")
        schedule.clear()
        conn = create_connection(self.dbname)
        cur = conn.cursor()

        cur.execute("SELECT * FROM picron WHERE enabled=1")

        rows = cur.fetchall()
        logging.debug(f'PiCron: all jobs: {rows}')
        for row in rows:
            # id = row[0]
            # name = row[1]
            schedule_name = row[2]
            schedule_parm = row[3]
            module_name = row[4]
            module_parm = row[5]

            if db_get_parm_conf(self.dbname, module_name, 'status') == 'on':
                try:
                    if schedule_name == 'second':
                        schedule.every().second.do(self.job, module_name, module_parm)
                    elif schedule_name == 'seconds':
                        schedule.every(int(schedule_parm)).seconds.do(self.job, module_name, module_parm)
                    elif schedule_name == 'minute':
                        schedule.every().minute.do(self.job, module_name, module_parm)
                    elif schedule_name == 'minutes':
                        schedule.every(int(schedule_parm)).minutes.do(self.job, module_name, module_parm)
                    elif schedule_name == 'minute.at':
                        schedule.every().minute.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'hour':
                        schedule.every().hour.do(self.job, module_name, module_parm)
                    elif schedule_name == 'hours':
                        schedule.every(int(schedule_parm)).hours.do(self.job, module_name, module_parm)
                    elif schedule_name == 'hour.at':
                        schedule.every().hour.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'day':
                        schedule.every().day.do(self.job, module_name, module_parm)
                    elif schedule_name == 'days':
                        schedule.every(int(schedule_parm)).days.do(self.job, module_name, module_parm)
                    elif schedule_name == 'day.at':
                        schedule.every().day.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'week':
                        schedule.every().week.do(self.job, module_name, module_parm)
                    elif schedule_name == 'weeks':
                        schedule.every(int(schedule_parm)).weeks.do(self.job, module_name, module_parm)
                    elif schedule_name == 'week.at':
                        schedule.every().week.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'monday':
                        schedule.every().monday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'monday.at':
                        schedule.every().monday.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'tuesday':
                        schedule.every().tuesday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'tuesday.at':
                        schedule.every().tuesday.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'wednesday':
                        schedule.every().wednesday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'wednesday.at':
                        schedule.every().wednesday.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'thursday':
                        schedule.every().thursday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'thursday.at':
                        schedule.every().thursday.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'friday':
                        schedule.every().friday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'friday.at':
                        schedule.every().friday.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'saturday':
                        schedule.every().saturday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'saturday.at':
                        schedule.every().saturday.at(schedule_parm).do(self.job, module_name, module_parm)
                    elif schedule_name == 'sunday':
                        schedule.every().sunday.do(self.job, module_name, module_parm)
                    elif schedule_name == 'sunday.at':
                        schedule.every().sunday.at(schedule_parm).do(self.job, module_name, module_parm)


                except Exception as e:
                    logging.error(f'PiCron: exception: {e}')

        conn.close()

    def job(self, module_name, module_parm):
        if module_name == 'GPIO':
            self.PDQ.add(json.loads(module_parm))
        elif module_name == 'SCRIPT':
            if os.path.exists(f'scripts/{module_parm}.script'):
                try:
                    status = subprocess.call(f'scripts/{module_parm}.script', shell=True)
                    logging.info(f'PiCron: script: {module_name}, module parm: {module_parm}.script, status: {status}')
                except Exception as e:
                    logging.warning(f'PiCron: script: {module_name}, module parm: {module_parm}, exception: {e}')
            else:
                logging.warning(f"PiCron: script: {module_name} don't exist")
        elif module_name == 'PLUGIN':
            try:
                plugin_class = self.LP.get(module_parm)
                if plugin_class is not False:
                    run_info = plugin_class.run()
                    logging.debug(f'PiCron: plugin: {module_name}, module parm: {module_parm}, status run: {run_info}')
            except Exception as e:
                logging.warning(f'PiCron: plugin: {module_name}, module parm: {module_parm}, exception: {e}')

    def run(self):
        if string_to_boolen(db_get_parm_conf(self.dbname, 'MAIN', 'wait_for_ntp_sync')):
            logging.info("PiCron: server is waiting for time synchronization ..")
            while True:
                if return_time_status():
                    break
                time.sleep(60)
        logging.info("PiCron: server is ready and running..")
        self.setJobs()
        while True:
            schedule.run_pending()
            cmd = self.PCQ.get()
            if cmd is not None:
                logging.info(f"PiCron: commands: {cmd}")
                for key in list(cmd):
                    if key == 'PICRON':
                        if cmd[key][0] == 'RESTART':
                            logging.info("PiCron: restart")
                            sys.exit()
                        elif cmd[key][0] == 'LOCAL_SYNC':
                            self.setJobs()
            else:
                time.sleep(1)


class PiDeamonQueue(PiCronQueue):
    def __init__(self, size):
        self.cmd_queue = deque([])
        self.lock = threading.Lock()
        self.size = size


class PiDeamon(threading.Thread):
    def __init__(self, PCQ, PGD, P, dbname):
        threading.Thread.__init__(self)
        self.PGD = PGD
        self.PCQ = PCQ
        self.P = P
        self.dbname = dbname
        self.gpio_status = db_get_parm_conf(self.dbname, 'GPIO', 'status')
        if self.gpio_status == 'on':
            self.PG = PiGpio(self.dbname)

        self.setDaemon(True)

    def run(self):
        logging.info("PiDeamon: server is ready and running..")
        while True:
            commands = self.PGD.get()
            if commands is not None:
                logging.info(f"PiDeamon: commands: {commands}")
                for key in list(commands):
                    if key == 'PIDEAMON':
                        if commands['PIDEAMON'][0] == 'RESTART':
                            logging.info("PiDeamon: restart")
                            subprocess.call('/bin/systemctl restart smallcube', shell=True)
                        elif commands['PIDEAMON'][0] == 'PIREBOOT':
                            logging.info("PiDeamon: rebooting PI")
                            subprocess.call('/sbin/reboot', shell=True)
                        elif commands['PIDEAMON'][0] == 'PIUPGRADE':
                            logging.info("PiDeamon: start upgrade")
                            p1 = subprocess.Popen(['apt-get', 'update'])
                            p1.wait()
                            p2 = subprocess.Popen(['apt-get', '-y', 'upgrade'])
                            p2.wait()
                        elif commands['PIDEAMON'][0] == 'RELOAD_PLUGINS':
                            logging.info("PiDeamon: reload plugins")
                            self.P.reload()
                        if commands['PIDEAMON'][0] == 'RESTART_FLASK':
                            time.sleep(1)
                            subprocess.call('/bin/systemctl restart api_smallcube', shell=True)
                            logging.info("PiDeamon: restart api")
                    elif key == 'GPIO' and self.gpio_status == 'on':
                        self.PG.gpio_job(commands['GPIO'])
            else:
                time.sleep(0.1)


class PiGpio:
    def __init__(self, dbname):
        self.dbname = dbname
        self.reset()
        self.set_conf()
        self.load_pin_conf_from_db()
        self.load_pin_status_from_db()

    def set_conf(self):
        if db_get_parm_conf(self.dbname, 'GPIO', 'gpio_setwarnings') == 'True':
            GPIO.setwarnings(True)
        else:
            GPIO.setwarnings(False)
        setmode = db_get_parm_conf(self.dbname, 'GPIO', 'gpio_setmode')
        logging.info(f"PiGpio: setting setmode: {setmode}")
        if setmode == 'board':
            try:
                GPIO.setmode(GPIO.BOARD)
            except Exception as e:
                logging.info(f"PiGpio: {e}")
        elif setmode == 'bcm':
            try:
                GPIO.setmode(GPIO.BCM)
            except Exception as e:
                logging.info(f"PiGpio: {e}")

    def reset(self):
        GPIO.cleanup()

    def load_pin_status_from_db(self):
        conn = create_connection(self.dbname)
        cur = conn.cursor()
        cur.execute('SELECT pin_number, pin_status FROM gpio WHERE enabled=1 and pin_conf="GPIO.OUT"')
        rows = cur.fetchall()
        for r in rows:
            pin_number = r[0]
            pin_status = r[1]
            if pin_status == '1' or pin_status == '0':
                cmd = ['GPIO.output', {pin_number: int(pin_status)}]
                self.gpio_job(cmd, sync_db=False)
        conn.close()

    def load_pin_conf_from_db(self):
        conn = create_connection(self.dbname)
        cur = conn.cursor()
        cur.execute('SELECT pin_number, pin_conf FROM gpio WHERE enabled=1')
        rows = cur.fetchall()
        for r in rows:
            pin_number = r[0]
            pin_conf = r[1]
            cmd = ['GPIO.setup', {pin_number: pin_conf}]
            self.gpio_job(cmd, sync_db=False)
        conn.close()

    def gpio_job(self, job, sync_db=True):
        logging.info(f"PiGpio: setting gpio: {job}")
        if db_get_parm_conf(self.dbname, 'GPIO', 'status') == 'on':
            command = job[0]
            command_val = job[1]
            for pin in list(command_val.keys()):
                pin_val = command_val[pin]
                pin_int = int(pin)
                enabled = db_get_parm_gpio(self.dbname, pin_int, 'enabled')
                if enabled == 1:
                    if command == 'GPIO.setup':
                        if pin_val == 'GPIO.OUT':
                            try:
                                GPIO.setup(pin_int, GPIO.OUT, initial=GPIO.HIGH)
                                GPIO.setup(pin_int, GPIO.OUT)
                            except Exception as e:
                                logging.error(f"PiGpio: setup exception: {e}")
                                return False
                            else:
                                if sync_db:
                                    db_set_gpio_conf(self.dbname, pin_int, 'GPIO.OUT')
                        elif pin_val == 'GPIO.IN':
                            try:
                                GPIO.setup(pin_int, GPIO.IN)
                            except Exception as e:
                                logging.error(f"PiGpio: setup exception: {e}")
                                return False
                            else:
                                if sync_db:
                                    db_set_gpio_conf(self.dbname, pin_int, 'GPIO.IN')
                    elif command == 'GPIO.output':
                        try:
                            GPIO.output(pin_int, pin_val)
                        except Exception as e:
                            logging.error(f"PiGpio: output exception: {e}")
                            return False
                        else:
                            if sync_db:
                                db_set_gpio_status(self.dbname, pin_int, pin_val)
                    elif command == 'GPIO.input':
                        try:
                            input_status = GPIO.input(pin_int)
                        except Exception as e:
                            logging.error(f"PiGpio: input exception: {e}")
                            return False
                        else:
                            if sync_db:
                                db_set_gpio_status(self.dbname, pin_int, input_status)
                else:
                    logging.warning(f"PiGpio: pin {pin} is disabled")


class Plugins:
    def __init__(self, dbname):
        self.dbname = dbname
        self.loaded_plugins = {}
        self.ena_plugin = []
        self.dis_plugin = []
        self.reload()

    def get(self, class_name):
        if class_name in self.loaded_plugins:
            return self.loaded_plugins[class_name]
        else:
            return False

    def reload(self):
        plugins_dir = 'plugins'
        plugins = next(os.walk(plugins_dir))[1]
        logging.debug(f"LoadPlugins, plugins folder: {plugins}")
        bad_class_name = ['MAIN', 'PI_TALK', 'GPIO', 'SCRIPT', 'PLUGIN']
        for p in plugins:
            if p != '__pycache__':
                try:
                    with open(f'{plugins_dir}/{p}/conf.json') as handle:
                        data = json.load(handle)
                        name = data['class']
                        enabled = data['enabled']
                except Exception as e:
                    logging.warning(f"LoadPlugins, plugin {p}, {e}")
                else:
                    if name in bad_class_name:
                        logging.warning(f"LoadPlugins, bad class name: {name} is banned, {e}")
                        continue
                    if enabled == '1':
                        try:
                            plugin_class = locate(f'{plugins_dir}.{p}.file_class.{name}')
                            class_instance = plugin_class(self.dbname)
                            if db_get_parm_conf(self.dbname, name, 'installed') is None:
                                class_instance.install()
                            self.loaded_plugins[name] = class_instance
                            self.ena_plugin.append(name)

                        except Exception as e:
                            logging.warning(f"LoadPlugins, class {name}, {e}")
                        else:
                            logging.info(f"LoadPlugins, loaded plugin {name} done")
                    elif enabled == '0':
                        try:
                            if db_get_parm_conf(self.dbname, name, 'installed') is not None:
                                plugin_class = locate(f'{plugins_dir}.{p}.file_class.{name}')
                                class_instance = plugin_class(self.dbname)
                                class_instance.uninstall()
                        except Exception as e:
                            logging.warning(f"LoadPlugins, class {name}, {e}")
                        self.dis_plugin.append(name)
        db_add_plugins(self.ena_plugin, self.dis_plugin)


class SystemdHandler(logging.Handler):
    PREFIX = {
        # EMERG <0>
        # ALERT <1>
        logging.CRITICAL: "<2>",
        logging.ERROR: "<3>",
        logging.WARNING: "<4>",
        # NOTICE <5>
        logging.INFO: "<6>",
        logging.DEBUG: "<7>",
        logging.NOTSET: "<7>"
    }

    def __init__(self, stream=sys.stdout):
        self.stream = stream
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            msg = self.PREFIX[record.levelno] + self.format(record)
            msg = msg.replace("\n", "\\n")
            self.stream.write(msg + "\n")
            self.stream.flush()
        except Exception:
            self.handleError(record)


if __name__ == '__main__':
    # root_logger = logging.getLogger()
    # root_logger.setLevel("ERROR")
    # root_logger.addHandler(SystemdHandler())

    base_path = os.path.dirname(os.path.abspath(__file__))

    logging.basicConfig(level=logging.WARNING,
                        # filename=base_path + '/static/logs/' + os.path.basename(__file__) + '.log',
                        filename=os.path.basename(__file__) + '.log',
                        format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                        style="{")

    SC = SmallCube()
    SC.start()
