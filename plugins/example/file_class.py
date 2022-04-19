from utils import *

# change name of plugin class
class ex:
    '''
    Example class
    '''

    def __init__(self, dbname):
        self.dbname = dbname
        self.name = type(self).__name__
        # add below your code

    def run(self):
        '''
        Add your code to do some thing here.
        :return: String - its used for log
        '''
        return 'True'

    def install(self):
        '''
        Install db data for plugin or other stuff here
        :return:
        '''
        conn = create_connection(self.dbname)
        c = conn.cursor()
        c.execute(f"INSERT INTO conf VALUES (null, '{self.name}', 'installed', 'yes')")
        # Add your code here, dont remove line: c.execute(f"INSERT INTO conf VALUES (null, '{self.name}', 'installed', 'yes')")
        conn.commit()
        conn.close()

    def uninstall(self):
        '''
        Remove db scheme for plugin or other stuff here
        :return:
        '''
        conn = create_connection(self.dbname)
        c = conn.cursor()
        c.execute(f"DELETE FROM conf WHERE module_name='{self.name}'")
        # Add your code to delete here, dont remove line: c.execute(f"DELETE FROM conf WHERE module_name='{self.name}'")
        conn.commit()
        conn.close()
