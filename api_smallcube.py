import json

from utils import *
from flask import jsonify, request, Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import logging
import os

base_path = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.DEBUG,
                    # filename=base_path + '/static/logs/' + os.path.basename(__file__) + '.log',
                    filename=os.path.basename(__file__) + '.log',
                    format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                    style="{")

app = Flask(__name__)
auth = HTTPBasicAuth()
dbname = 'db.sql'

db_user = db_get_parm_conf(dbname, 'MAIN', 'user')
db_password = db_get_parm_conf(dbname, 'MAIN', 'pass')
USERS = {
    db_user: generate_password_hash(db_password)
}

ID_DEVICE = db_get_parm_conf(dbname, "MAIN", "id_device")


@auth.verify_password
def verify_password(username, password):
    if username in USERS and check_password_hash(USERS.get(username), password):
        logging.info(f"Api: verify_password: {username} logged in")
        return username
    else:
        logging.warning(f"Api: verify_password: invalid login attempt")
        return False


@app.route('/api/app/connect/<pin>', methods=['GET'])
def app_connect(pin):
    if db_get_parm_conf(dbname, 'MAIN', 'app_connected') == 'no':
        if pin == db_get_parm_conf(dbname, 'MAIN', 'pass'):
            id = db_get_parm_conf(dbname, 'MAIN', 'id_device')
            user = db_get_parm_conf(dbname, 'MAIN', 'user')
            return return_api({'id': id, 'user': user}, 200)
        else:
            logging.info(f"Api: app_connect: bad pin {pin}")
            return return_api('Bad pin', 404)
    else:
        logging.warning(f"Api: app_connect: App is connected")
        return return_api('App is connected', 404)


@app.route('/api/app/<id_device>/check', methods=['GET'])
@auth.login_required
def app_chcek(id_device):
    if db_get_parm_conf(dbname, "MAIN", "id_device") == id_device and db_get_parm_conf(dbname, 'MAIN',
                                                                                       'app_connected') == 'no':
        new_pin = pin_gen(4)
        db_set_parm_conf(dbname, 'MAIN', 'pass', new_pin)
        db_set_parm_conf(dbname, 'MAIN', 'app_connected', 'yes')
        cmd = restart_flask(id_device)
        msg = pideamon_talk(cmd)

        logging.debug(f"Api: app_connect: new pin {new_pin}")
        return return_api({'new_pin': new_pin}, 200)
    else:
        logging.warning(f"Api: app_connect: App is not connected")
        return return_api('App is not connected', 404)


@app.route('/api/<id_device>/system/piinfo', methods=['GET'])
@auth.login_required
def api_raspberrypi_info(id_device):
    """ Get Pi info:
        - hardware
        - up time
        - time and date

    :param id_device:
    :return: json (cpuinfo,uptime,time,time_sync)
    """
    if ID_DEVICE == id_device:
        cpuinfo = subprocess.getoutput('/bin/cat /proc/cpuinfo')
        uptime = subprocess.getoutput('/usr/bin/uptime')
        time_sync = return_time_status()
        now = datetime.datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return return_api({'cpuinfo': cpuinfo, 'uptime': uptime, 'time': dt_string, 'time_sync': time_sync}, 200)
    logging.warning(f"Api: get_raspberrypi_info: bad id_device {id_device}")
    return return_api('Bad id device', 404)


@app.route('/api/<id_device>/get/conf', methods=['GET'])
@auth.login_required
def api_get_conf(id_device):
    """ Get

    :param id_device:
    :return:
    """
    if ID_DEVICE == id_device:
        return return_api(db_get_conf(dbname), 200)
    else:
        logging.warning(f"Api: api_system_info_id_list: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/get/conf/status', methods=['POST'])
@auth.login_required
def api_get_conf_status(id_device):
    """ Get

    :param id_device:
    :return:
    """
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
            mod = data['mod']
            parm = data['parm']
        except Exception as e:
            return return_api(f'Data is not json, {e}', 404)
        else:
            val = {"val": str(db_get_parm_conf(dbname, mod, parm))}
            return return_api(val, 200)
    else:
        logging.warning(f"Api: api_system_info_id_list: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/set/conf', methods=['PUT'])
@auth.login_required
def api_set_conf(id_device):
    """

    :param id_device:
    :return:
    """
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                module_name = data['module_name']
                name = data['name']
                val = data['val']
            except Exception as e:
                return return_api('Bad name pin or', 404)
            else:
                try:
                    db_set_parm_conf(dbname, module_name, name, val)
                except Exception as e:
                    return return_api(f'{e}', 404)
                else:
                    return return_api('OK', 200)
    else:
        logging.warning(f"Api: api_system_info_id_list: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio', methods=['GET'])
@auth.login_required
def api_gpio_list(id_device):
    if ID_DEVICE == id_device:
        return return_api(db_get_gpio(dbname), 200)
    else:
        logging.warning(f"Api: api_gpio_pin_number: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/<int:pin>', methods=['GET'])
@auth.login_required
def api_gpio_info(id_device, pin):
    if ID_DEVICE == id_device:
        pin_info = db_get_parm_gpio(dbname, pin, False)
        logging.info(f"Api: api_gpio: pin_info: {pin}")
        return return_api(pin_info, 200)
    else:
        logging.warning(f"Api: api_gpio_input: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/setup', methods=['PUT'])
@auth.login_required
def api_gpio_setup(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                pin = data['pin']
                pin_set = data['setup']
            except Exception as e:
                return return_api('Bad name pin or', 404)
            else:
                if db_get_parm_gpio(dbname, pin, 'enabled') == 1:
                    # ([id, 'PIDEAMON', {'GPIO':['GPIO.setup',{'24':'GPIO.OUT'}]}])
                    cmd = [id_device, 'PIDEAMON', {'GPIO': ['GPIO.setup', {pin: pin_set}]}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)
                else:
                    return return_api(f'Pin {pin} is disabled, enable first', 404)
    else:
        logging.warning(f"Api: api_gpio_setup: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/output', methods=['PUT'])
@auth.login_required
def api_gpio_output(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                pin = data['pin']
                output = data['output']
            except Exception as e:
                return return_api(f'Bad name pin or output, {e}', 404)
            else:
                if db_get_parm_gpio(dbname, pin, 'enabled') == 1:
                    cmd = [id_device, 'PIDEAMON', {'GPIO': ['GPIO.output', {pin: output}]}]
                    logging.debug(cmd)
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)
                else:
                    return return_api(f'Pin {pin} is disabled, enable first', 404)
    else:
        logging.warning(f"Api: api_gpio_output: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/input/<int:pin>', methods=['GET'])
@auth.login_required
def api_gpio_input(id_device, pin):
    if ID_DEVICE == id_device:
        pin_status = db_get_parm_gpio(dbname, pin, 'pin_status')
        logging.info(f"Api: api_gpio_input: pin_status {pin_status}")
        return return_api(pin_status, 200)
    else:
        logging.warning(f"Api: api_gpio_input: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/enable/<int:pin>', methods=['PUT'])
@auth.login_required
def api_gpio_enable(id_device, pin):
    if ID_DEVICE == id_device:
        db_set_gpio_enabled(dbname, pin, 1)
        return return_api('OK', 200)
    else:
        logging.warning(f"Api: api_gpio_enable: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/disable/<int:pin>', methods=['PUT'])
@auth.login_required
def api_gpio_disable(id_device, pin):
    if ID_DEVICE == id_device:
        db_set_gpio_enabled(dbname, pin, 0)
        return return_api('OK', 200)
    else:
        logging.warning(f"Api: api_gpio_disable: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/gpio/name/<int:pin>', methods=['PUT'])
@auth.login_required
def api_gpio_name(id_device, pin):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                name = data['name']
            except Exception as e:
                return return_api('Bad key', 404)
            else:
                db_set_gpio_name(dbname, pin, name)
                return return_api('OK', 200)
    else:
        logging.warning(f"Api: api_gpio_name: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler', methods=['GET'])
@auth.login_required
def api_scheduler_list(id_device):
    job_dict = {}
    if ID_DEVICE == id_device:
        for i, r in enumerate(db_get_scheduler(dbname)):
            id = r[0]
            name = r[1]
            sch_name = r[2]
            sch_parm = r[3]
            module = r[4]
            parm = r[5]
            enabled = r[6]
            if module == "GPIO":
                parm = convert_sch_parm(parm)
                parm["id"] = id
                parm["name"] = name
                parm["sch_name"] = sch_name
                parm["sch_parm"] = sch_parm
                parm["module"] = module
                parm["enabled"] = enabled
                job_dict[i] = parm
            else:
                job_dict[i] = {"id": id, "name": name, "sch_name": sch_name, "sch_parm": sch_parm, "module": module,
                               "parm": parm, "enabled": enabled}
        return return_api(job_dict, 200)
        # return return_api(db_get_scheduler(dbname), 200)
    else:
        logging.warning(f"Api: api_scheduler_list: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/<int:id>', methods=['GET'])
@auth.login_required
def api_scheduler_id(id_device, id):
    if ID_DEVICE == id_device:
        job_info = db_get_scheduler_job(dbname, id, False)
        if job_info['module_name'] == 'HT':
            return return_api(job_info, 200)
        if job_info['python_module'] == 1:
            module_parm = json.loads(job_info['module_parm'])
            gpio_output = gpio_output_to_api(module_parm)
            job_info['pin'] = gpio_output['pin']
            job_info['val'] = gpio_output['val']
            del job_info['module_parm']
            logging.info(f"Api: api_scheduler_id: {job_info}")
            return return_api(job_info, 200)
        elif job_info['python_module'] == 0:
            return return_api(job_info, 200)
    else:
        logging.warning(f"Api: api_scheduler_id: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/add/script', methods=['POST'])
@auth.login_required
def api_scheduler_add_script(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                logging.debug(f'api_scheduler_add: {data}')
                name = data['name']
                schedule_name = data['schedule_name']
                schedule_parm = data['schedule_parm']
                module_name = data['module_name']
                module_parms = data['script_name']
                enabled = data['enabled']
            except Exception as e:
                return return_api('Bad json data', 404)
            else:
                new_id = db_add_scheduler_job(dbname, name, schedule_name, schedule_parm, module_name, module_parms,
                                              enabled)

                cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                msg = pideamon_talk(cmd)
                if msg:
                    return return_api('OK', 200)
                else:
                    return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_gpio_output: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/add/plugin', methods=['POST'])
@auth.login_required
def api_scheduler_add_plugin(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                logging.debug(f'api_scheduler_add: {data}')
                name = data['name']
                schedule_name = data['schedule_name']
                schedule_parm = data['schedule_parm']
                module_name = data['module_name']
                module_parms = data['script_name']
                enabled = data['enabled']
            except Exception as e:
                return return_api('Bad json data', 404)
            else:
                new_id = db_add_scheduler_job(dbname, name, schedule_name, schedule_parm, module_name, module_parms,
                                              enabled)

                cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                msg = pideamon_talk(cmd)
                if msg:
                    return return_api('OK', 200)
                else:
                    return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_gpio_output: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/add/gpio', methods=['POST'])
@auth.login_required
def api_scheduler_add_gpio(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            try:
                logging.debug(f'api_scheduler_add: {data}')
                name = data['name']
                schedule_name = data['schedule_name']
                schedule_parm = data['schedule_parm']
                module_name = data['module_name']
                pin = data['pin']
                pin_val = data['pin_val']
                module_parms = {module_name: ['GPIO.output', {pin: int(pin_val)}]}
                enabled = data['enabled']
            except Exception as e:
                return return_api('Bad json data', 404)
            else:
                new_id = db_add_scheduler_job(dbname, name, schedule_name, schedule_parm, module_name, module_parms,
                                              enabled)

                cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                msg = pideamon_talk(cmd)
                if msg:
                    return return_api('OK', 200)
                else:
                    return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_gpio_output: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/update', methods=['PUT'])
@auth.login_required
def api_scheduler_update(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
            id = data['id']
            name = data['name']
            module_name = data['module_name']
            module_parms = data['module_parms']
            schedule_name = data['schedule_name']
            schedule_parm = data['schedule_parm']
            enabled = data['enabled']
        except Exception as e:
            return return_api('Data is not json', 404)
        else:
            # {'name': 'Name', 'module_name': 'SCRIPT', 'module_parms': 'simple', 'schedule_name': 'minutes', 'schedule_parm': '1', 'enabled': '0', 'id': 5}
            db_update_scheduler_job(db, id, name, module_name, module_parms, schedule_name, schedule_parm, enabled)
            cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
            msg = pideamon_talk(cmd)
            if msg:
                return return_api('OK', 200)
            else:
                return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_scheduler_update: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scheduler/delete/<int:id>', methods=['DELETE'])
@auth.login_required
def api_scheduler_delete(id_device, id):
    if ID_DEVICE == id_device:
        db_del_scheduler_job(dbname, id)
        logging.info(f"Api: api_scheduler_delete: {id}")
        cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
        msg = pideamon_talk(cmd)
        if msg:
            return return_api('OK', 200)
        else:
            return return_api(f'Incorrect commands', 404)
    else:
        logging.warning(f"Api: api_scheduler_delete: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/log/show/<log_name>', methods=['GET'])
@auth.login_required
def api_get_logs(id_device, log_name):
    if ID_DEVICE == id_device:
        try:
            with open(log_name) as f:
                log = f.read()
        except Exception as e:
            return return_api(f'api_deamon, {e}', 404)
        else:
            return return_api(log, 200)
    else:
        logging.warning(f"Api: api_deamon: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/get/plugin/data/<plugin_name>/<name>', methods=['GET'])
@auth.login_required
def api_get_plugin_data(id_device, plugin_name, name):
    if ID_DEVICE == id_device:
        try:
            plugin_data = json.loads(db_get_plugin_data(dbname, plugin_name, name))
        except Exception as e:
            logging.warning(f"Api: api_get_plugin_data, {e}")
            return return_api(f"Api: api_get_plugin_data, {e}", 404)
        return return_api(plugin_data, 200)
    else:
        logging.warning(f"Api: api_get_plugin_data: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/daemon', methods=['PUT'])
@auth.login_required
def api_deamon(id_device):
    if ID_DEVICE == id_device:
        try:
            data = request.get_json()
            module_name = data['module_name']
            cmd = data['cmd']
        except Exception as e:
            return return_api(f'api_deamon, {e}', 404)
        else:
            if module_name == 'PICRON':
                if cmd == 'RESTART':
                    # cmd = [id_device, 'PICRON', {'PICRON': ['RESTART']}]
                    cmd = restart_picron(id_device)
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)

                elif cmd == 'LOCAL_SYNC':
                    cmd = [id_device, 'PICRON', {'PICRON': ['LOCAL_SYNC']}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)
            elif module_name == 'PIDEAMON':
                if cmd == 'RESTART':
                    # cmd = [id_device, 'PIDEAMON', {'PIDEAMON': ['RESTART']}]
                    cmd = restart_pidaemon(id_device)
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)

                elif cmd == 'PIREBOOT':
                    cmd = [id_device, 'PIDEAMON', {'PIDEAMON': ['PIREBOOT']}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)

                elif cmd == 'PIUPGRADE':
                    cmd = [id_device, 'PIDEAMON', {'PIDEAMON': ['PIUPGRADE']}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)

                elif cmd == 'RESTART_FLASK':
                    cmd = [id_device, 'PIDEAMON', {'PIDEAMON': ['RESTART_FLASK']}]
                    msg = pideamon_talk(cmd)
                    if msg:
                        return return_api('OK', 200)
                    else:
                        return return_api(f'Incorrect commands', 404)

            else:
                return return_api(f'Incorrect daemon, {module_name}', 404)
    else:
        logging.warning(f"Api: api_deamon: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/plugins', methods=['GET'])
@auth.login_required
def api_get_plugins(id_device):
    if ID_DEVICE == id_device:
        return return_api(db_get_plugins(), 200)
    else:
        logging.warning(f"Api: api_deamon: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/scripts', methods=['GET'])
@auth.login_required
def api_get_scripts(id_device):
    if ID_DEVICE == id_device:
        return return_api(get_scripts_list(), 200)
    else:
        logging.warning(f"Api: api_deamon: bad id_device {id_device}")
        return return_api('Bad id device', 404)


@app.route('/api/<id_device>/ping', methods=['GET'])
@auth.login_required
def api_ping(id_device):
    if ID_DEVICE == id_device:
        return return_api('PONG', 200)
    else:
        logging.warning(f"Api: api_deamon: bad id_device {id_device}")
        return return_api('Bad id device', 404)


def return_api(data, status):
    resp = jsonify(data)
    resp.status_code = status
    return resp
