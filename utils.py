import logging
import sqlite3
import socket
import json
import subprocess
import string
import secrets
import socket
import glob

db = 'db.sql'


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        logging.error(f"create_connection: {e}")
    return conn


def db_get_conf_by_id(db, id):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM conf WHERE id=?', (id,))
    rows = cur.fetchall()
    conn.close()
    return rows[0]


# def db_get_parm_conf(db, module_name, name):
#     conn = create_connection(db)
#     cur = conn.cursor()
#     cur.execute('SELECT value FROM conf WHERE module_name=? and name=?', (module_name, name))
#     rows = cur.fetchall()
#     val = rows[0][0]
#     conn.close()
#     return val

def db_get_parm_conf(db, module_name, name):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT value FROM conf WHERE module_name=? and name=?', (module_name, name))
    rows = cur.fetchall()
    if len(rows) > 0:
        val = rows[0][0]
        conn.close()
        return val
    else:
        return None


def db_get_conf(db):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM conf')
    rows = cur.fetchall()
    conn.close()
    return rows


def db_set_parm_conf(db, module_name, name, val):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('UPDATE conf SET value = ? WHERE module_name=? and name=?', (val, module_name, name))
    conn.commit()
    conn.close()


def db_get_plugin_data(db, plugin_name, name):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT data FROM plugins_data WHERE plugin_name=? and name=?', (plugin_name, name))
    rows = cur.fetchall()
    if len(rows) > 0:
        val = rows[0][0]
        conn.close()
        return val
    else:
        return None


def db_set_plugin_data(db, plugin_name, name, data):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('UPDATE plugins_data SET data = ? WHERE plugin_name=? and name=?', (data, plugin_name, name))
    conn.commit()
    conn.close()


def db_get_gpio(db):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM gpio')
    rows = cur.fetchall()
    conn.close()
    return rows


def db_get_parm_gpio(db, pin, key):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM gpio WHERE pin_number=?', (pin,))
    rows = cur.fetchall()
    status = {'id': rows[0][0], 'name': rows[0][1], 'pin_number': rows[0][2], 'pin_conf': rows[0][3],
              'pin_status': rows[0][4], 'enabled': rows[0][5]}
    conn.close()
    if key is False:
        return status
    else:
        try:
            return status[key]
        except Exception as e:
            logging.error(f"get_pin_info: bad key, exception:  {e}")


def db_set_gpio_status(db, pin, pin_status):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('UPDATE gpio SET pin_status = ? WHERE pin_number=?', (pin_status, pin))
    conn.commit()
    conn.close()


def db_set_gpio_enabled(db, pin, enabled):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('UPDATE gpio SET enabled = ? WHERE pin_number=?', (enabled, pin))
    conn.commit()
    conn.close()


def db_set_gpio_conf(db, pin, pin_conf):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('UPDATE gpio SET pin_conf = ? WHERE pin_number=?', (pin_conf, pin))
    conn.commit()
    conn.close()


def db_set_gpio_name(db, pin, name):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('UPDATE gpio SET name = ? WHERE pin_number=?', (name, pin))
    conn.commit()
    conn.close()


'''
def db_get_id(db, table_name):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute(f'SELECT id FROM {table_name}')
    rows = cur.fetchall()
    id_list = []
    for r in rows:
        id_list.append(r[0])
    conn.close()
    return id_list
'''


def db_get_scheduler(db):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM picron')
    rows = cur.fetchall()
    conn.close()
    return rows


def db_get_scheduler_job(db, id, key):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM picron WHERE id=?', (id,))
    rows = cur.fetchall()
    status = {'id': rows[0][0], 'name': rows[0][1], 'schedule_name': rows[0][2], 'schedule_parm': rows[0][3],
              'module_name': rows[0][4], 'module_parm': rows[0][5], 'enabled': rows[0][6]}
    conn.close()
    if key is False:
        return status
    else:
        try:
            return status[key]
        except Exception as e:
            logging.error(f"get_scheduler_info: bad key, exception:  {e}")


def db_add_scheduler_job(db, name, schedule_name, schedule_parm, module_name, module_parms, enabled):
    conn = create_connection(db)
    cur = conn.cursor()
    if module_name == 'GPIO':
        # {'GPIO': ['GPIO.output', {pin: output}]}
        # module = {module_name: [module_parms, {pin: pin_val}]}
        # module = {module_name: [module_parms, {pin: pin_val}]}
        cur.execute('INSERT INTO picron VALUES (null, ?, ?, ?, ?, ?, ?)',
                    (name, schedule_name, schedule_parm, module_name, json.dumps(module_parms), enabled))

    elif module_name == 'SCRIPT':
        cur.execute('INSERT INTO picron VALUES (null, ?, ?, ?, ?, ?, ?)',
                    (name, schedule_name, schedule_parm, module_name, module_parms, enabled))
    elif module_name == 'PLUGIN':
        cur.execute('INSERT INTO picron VALUES (null, ?, ?, ?, ?, ?, ?)',
                    (name, schedule_name, schedule_parm, module_name, module_parms, enabled))

    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def db_update_scheduler_job(db, id, name, module_name, module_parms, schedule_name, schedule_parm, enabled):
    conn = create_connection(db)
    cur = conn.cursor()
    # {'name': 'Name', 'module_name': 'SCRIPT', 'module_parms': 'simple', 'schedule_name': 'minutes', 'schedule_parm': '1', 'enabled': '0', 'id': 5}
    cur.execute(
        'UPDATE picron SET name = ?, module_name=?, module_parms=?, schedule_name=?, schedule_parm=?, enabled=? WHERE id=?',
        (name, module_name, module_parms, schedule_name, schedule_parm, enabled, id))
    conn.commit()
    conn.close()


def db_del_scheduler_job(db, id):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('DELETE FROM picron WHERE id=?', (id,))
    conn.commit()
    conn.close()


def db_add_plugins(ena_plugin, dis_plugin):
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('DELETE FROM plugins')
    for e in ena_plugin:
        cur.execute("INSERT INTO plugins VALUES (null,?,?,?)", (e, 'status', 1))
    for e in dis_plugin:
        cur.execute("INSERT INTO plugins VALUES (null,?,?,?)", (e, 'status', 0))
    conn.commit()
    conn.close()


def db_get_plugins():
    conn = create_connection(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM plugins')
    rows = cur.fetchall()
    conn.close()
    return rows


def gpio_output_to_api(gpio):
    gpio_output = gpio['GPIO'][1]
    for pin in gpio_output:
        val = gpio_output[pin]
    return {'pin': pin, 'val': val}


def string_to_boolen(string):
    if string == 'False':
        return False
    elif string == 'True':
        return True


def return_time_status():
    status = subprocess.getoutput('/usr/bin/timedatectl show --property=NTPSynchronized --value')
    if status == 'yes':
        logging.info(f"return_time_status: System time is synchronized")
        return True
    else:
        logging.warning(f"return_time_status: System time is not synchronized")
        return False


def pideamon_talk(cmd):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect("smallcube.sock")
        s.settimeout(1)
        # data=json.dumps([id, 'PIDEAMON', {'GPIO':['GPIO.setup',{'24':'GPIO.OUT'}]}])
        data = json.dumps(cmd)
        bytes_data = data.encode()
        s.send(bytes_data)
        try:
            msg = json.loads(s.recv(1024))
            if msg[0] == 'OK':
                return True
            else:
                return False
        except ValueError as e:
            logging.warning(f"pideamon_talk: received data is not json, {e}")
    except IOError as e:
        print(f'Cant connect {e}')
    finally:
        s.close()


def pass_gen(x, y):
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(x))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= y):
            break
    return password


def pin_gen(x):
    return ''.join(secrets.choice(string.digits) for i in range(x))


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def cmd_gpio_high(id_dev, pin):
    return [id_dev, 'PIDEAMON', {'GPIO': ['GPIO.output', {pin: 0}]}]


def cmd_gpio_low(id_dev, pin):
    return [id_dev, 'PIDEAMON', {'GPIO': ['GPIO.output', {pin: 1}]}]


def restart_picron(id_device):
    return [id_device, 'PICRON', {'PICRON': ['RESTART']}]


def restart_pidaemon(id_device):
    return [id_device, 'PIDEAMON', {'PIDEAMON': ['RESTART']}]


def restart_flask(id_device):
    return [id_device, 'PIDEAMON', {'PIDEAMON': ['RESTART_FLASK']}]


def convert_sch_parm(parm):
    parm = json.loads(parm)
    gpio_conf = parm['GPIO'][0]
    pin_conf = parm['GPIO'][1]
    for pin in pin_conf:
        pin_val = pin_conf[pin]
    return {"gpio_conf": gpio_conf, "pin": pin, "pin_val": pin_val}


def get_formated_scheduler_parm(schedule_name, x, h, m, s):
    h = str(int(h))
    m = str(int(m))
    s = str(int(s))

    if len(h) == 1:
        h = f'0{h}'
    elif len(h) == 2:
        h = f'{h}'

    if len(m) == 1:
        m = f'0{m}'
    elif len(m) == 2:
        m = f'{m}'

    if len(s) == 1:
        s = f'0{s}'
    elif len(s) == 2:
        s = f'{s}'

    if schedule_name == 'minutes' or schedule_name == 'hours' or schedule_name == 'days':
        return str(x)
    elif schedule_name == 'minute.at':
        return f':{s}'
    elif schedule_name == 'hour.at':
        return f':{m}:{s}'
    elif schedule_name == 'day.at':
        return f'{h}:{m}:{s}'


def get_scripts_list():
    tmp = glob.glob("scripts/*.script")
    scripts_list = []
    for t in tmp:
        t = t.split('/')
        t = t[1].split('.')
        scripts_list.append(t[0])

    return scripts_list
