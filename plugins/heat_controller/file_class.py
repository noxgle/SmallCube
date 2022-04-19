from utils import *
import json
import time
import w1thermsensor
import logging


class HeatController:

    def __init__(self, dbname):
        self.dbname = dbname
        self.name = type(self).__name__

        self.max_history_temp = 10080
        self.hysteresis_temp=1

    def run(self):
        id_device = db_get_parm_conf(self.dbname, "MAIN", "id_device")
        pin = str(db_get_parm_conf(self.dbname, self.name, 'gpio'))
        target_temp = int(db_get_parm_conf(self.dbname, self.name, 'temp'))
        sensor_temp = float(self.get_sensor_temp())

        temp_history = json.loads(db_get_plugin_data(self.dbname, self.name, 'temp_history'))
        temp_history[str(time.time())] = str(sensor_temp)

        size_temp_history = len(temp_history)
        if size_temp_history > self.max_history_temp:
            temp_history = dict(list(temp_history.items())[(size_temp_history - self.max_history_temp):])

        temp_history = json.dumps(temp_history)
        db_set_plugin_data(self.dbname, self.name, 'temp_history', temp_history)

        log = f"Sensor temp: {target_temp}. "

        if sensor_temp < target_temp:
            cmd = cmd_gpio_high(id_device, pin)
            msg = pideamon_talk(cmd)
            log = log + f"HeatController: to cold - ON, {msg} "
        elif sensor_temp > target_temp:
            cmd = cmd_gpio_low(id_device, pin)
            msg = pideamon_talk(cmd)
            log = log + f"HeatController: to hot - OFF, {msg} "
        return log

    def install(self):
        conn = create_connection(self.dbname)
        c = conn.cursor()
        c.execute(f"INSERT INTO conf VALUES (null, '{self.name}', 'installed', 'yes')")

        jsondata = json.dumps({})
        c.execute(f"INSERT INTO conf VALUES (null, '{self.name}', 'gpio', '')")
        c.execute(f"INSERT INTO conf VALUES (null, '{self.name}', 'temp', '')")
        c.execute(f"INSERT INTO plugins_data VALUES (null, '{self.name}', 'temp_history', '{jsondata}')")
        conn.commit()
        conn.close()

    def uninstall(self):
        conn = create_connection(self.dbname)
        c = conn.cursor()
        c.execute(f"DELETE FROM conf WHERE module_name='{self.name}'")
        c.execute(f"DELETE FROM picron WHERE module_parms='{self.name}'")
        c.execute(f"DELETE FROM plugins_data WHERE module_parms='{self.name}'")
        conn.commit()
        conn.close()

    def get_sensor_temp(self):
        sensor = w1thermsensor.W1ThermSensor()
        return sensor.get_temperature()
