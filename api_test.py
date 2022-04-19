import requests
import sys
from utils import *

URL = 'http://127.0.0.1:5080'
#URL = 'http://127.0.0.1:5000'
dbname = 'db.sql'
ID = db_get_parm_conf(dbname, 'MAIN', 'id_device')
user = db_get_parm_conf(dbname, 'MAIN', 'user')
password = db_get_parm_conf(dbname, 'MAIN', 'pass')

print(ID)
print(user)
print(password)


def enable_gpio_module():
    print('\nenable_gpio_module:')
    req = requests.put(url=f'{URL}/api/{ID}/set/conf', auth=(user, password),
                       json={'module_name': 'GPIO', 'name': 'status', 'val': 'on'})
    if req.status_code == 200:
        data = req.json()
        print(data)


def enable_script_module():
    print('\nenable_script_module:')
    req = requests.put(url=f'{URL}/api/{ID}/set/conf', auth=(user, password),
                       json={'module_name': 'SCRIPT', 'name': 'status', 'val': 'on'})
    if req.status_code == 200:
        data = req.json()
        print(data)


def enable_gpio(x):
    print('\nenable_gpio:')
    req = requests.put(url=f'{URL}/api/{ID}/gpio/enable/{x}', auth=(user, password), json={})
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        print(req.status_code)


def set_out_gpio(x):
    print('\nset_out_gpio:')
    req = requests.put(url=f'{URL}/api/{ID}/gpio/setup', auth=(user, password),
                       json={'pin': f'{x}', 'setup': 'GPIO.OUT'})
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        print(req.status_code)


def set_gpio_high(x):
    print('\nset_gpio_high:')
    req = requests.put(url=f'{URL}/api/{ID}/gpio/output', auth=(user, password),
                       json={'pin': f'{x}', 'output': 1})
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        data = req.json()
        print(data)
        print(req.status_code)


def set_gpio_low(x):
    print('\nset_gpio_low:')
    req = requests.put(url=f'{URL}/api/{ID}/gpio/output', auth=(user, password),
                       json={'pin': f'{x}', 'output': 0})
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        print(req.status_code)


def reload_conf():
    print('\nreload_conf:')
    req1 = requests.put(url=f'{URL}/api/{ID}/daemon', auth=(user, password),
                        json={'module_name': 'PICRON', 'cmd': 'RESTART'})
    if req1.status_code == 200:
        data = req1.json()
        print(data)
    else:
        print(req1.status_code)
        data = req1.json()
        print(data)

    req2 = requests.put(url=f'{URL}/api/{ID}/daemon', auth=(user, password),
                        json={'module_name': 'PIDEAMON', 'cmd': 'RESTART'})
    if req2.status_code == 200:
        data = req2.json()
        print(data)
    else:
        print(req2.status_code)


def add_scheduler_job():
    print('\nadd_scheduler_job:')
    req = requests.post(url=f'{URL}/api/{ID}/scheduler/add', auth=(user, password),
                        json={'name': 'simpletest', 'schedule_name': 'minutes', 'schedule_parm': '1', 'module_name': 'SCRIPT',
                              'module_parms': 'simple', 'enabled': '1'})
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        data = req.json()
        print(data)
        print(req.status_code)


'''
req = requests.get(url=f'{URL}/api/app/connect/{password}')
if req.status_code==200:
    data = req.json()
    print(data)
else:
    print(req.status_code)

req = requests.get(url=f'{URL}/api/app/{ID}/check',auth=(user,password))
if req.status_code==200:
    data = req.json()
    print(data)
else:
    print(req.status_code)

password = db_get_parm_conf(dbname, 'MAIN', 'pass')
req = requests.get(url=f'{URL}/api/{ID}/get/conf',auth=(user,password))
if req.status_code==200:
    data = req.json()
    print(data)
else:
    print(req.status_code)
'''

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '1':
            enable_gpio_module()
        elif sys.argv[1] == '1a':
            enable_script_module()
        elif sys.argv[1] == '2':
            enable_gpio(sys.argv[2])
        elif sys.argv[1] == '3':
            set_out_gpio(sys.argv[2])
        elif sys.argv[1] == '4':
            set_gpio_low(sys.argv[2])
        elif sys.argv[1] == '5':
            print(sys.argv[2])
            set_gpio_high(sys.argv[2])
        elif sys.argv[1] == '6':
            reload_conf()
        elif sys.argv[1] == '7':
            add_scheduler_job()

    print('\nConf:')
    req = requests.get(url=f'{URL}/api/{ID}/get/conf', auth=(user, password))
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        print(req.status_code)

    print('\nGpio:')
    req = requests.get(url=f'{URL}/api/{ID}/gpio', auth=(user, password))
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        print(req.status_code)

    print('\nScheduler:')
    req = requests.get(url=f'{URL}/api/{ID}/scheduler', auth=(user, password))
    if req.status_code == 200:
        data = req.json()
        print(data)
    else:
        print(req.status_code)

    print("""
Help:
enable gpio module in conf:
    api_test.py 1 
enable script module in conf:
    api_test.py 1a
enable gpio
    api_test.py 2 gpio_number
set gpio to out 
    api_test.py 3 gpio_number
set gpio status to low
    api_test.py 4 gpio_number
set gpio status to high
    api_test.py 5 gpio_number
reload configuration
    api_test.py 6
add job test to scheduler
    api_test.py 7
               """)
