from configobj import ConfigObj
import time
import os, platform
import requests


class bpi:
    def __init__(self, config):
        self.cfg = config
        self.last_state = True
        self.last_success = ''
        self.state = ''
        self.last_dc = ''
        self.last_check = ''
        self.log = open(self.cfg['bpi']['log'], 'a')
        if platform.system() == 'Linux':
            self.sys_ping = lambda adress: os.system('ping -c 1 -W 1 ' + adress + ' > /dev/null')
            self.cls = lambda: os.system('clear')
        if platform.system() == 'Windows':
            self.sys_ping = lambda adress: os.system('PING ' + adress + ' -n 1 -w 1000 > NUL')
            self.cls = lambda: os.system('cls')
        else:
            raise RuntimeError('OS not detected')

    def check_connection(self):
        self.last_check = time.strftime('%H:%M:%S')
        if self.sys_ping(cfg['bpi']['ping_adress']) == 0:
            self.state = 'SUCCESSFUL'
            if self.last_state == False:
                self.log.write(time.strftime('%a %d-%m-%Y %H:%M:%S')+' -> Reconnected\n')
                self.last_state = True
            return True
        else:
            self.state = 'FAILED'
            if self.last_state == True:
                self.log.write(time.strftime('%a %d-%m-%Y %H:%M:%S')+' -> Disconnected\n')
                self.last_dc = time.strftime('%H:%M:%S')
                self.last_state = False
            return False

    def send_credentials(self):
        try:
            requests.post(cfg['plug-inn']['host'],
                          data={
                              'auth_user': cfg['plug-inn']['username'],
                              'auth_pass': cfg['plug-inn']['password'],
                              'accept': 'Anmelden'
                          })
            self.log.write('\t' + time.strftime('%H:%M:%S') + ' -> PlugInn-Credentials have been transmitted\n')
            return True
        except requests.RequestException:
            self.log.write('\t' + time.strftime('%H:%M:%S') + ' -> Unexpected Transmission Error!!!\n')
            return False

    def start_watchdog(self):
        while True:
            has_connection = self.check_connection()
            time.sleep(1)
            if not has_connection:
                self.send_credentials()
                time.sleep(0.5)
            self.cls()
            print('Last Check: ' + self.last_check)
            print('Last Disconnect: ' + self.last_dc)
            print('CONNECTION INTEGRITY CHECK: ' + self.state)



if __name__ == '__main__':
    cfg = ConfigObj('bpi.ini')
    bpi_handler = bpi(cfg)
    bpi_handler.start_watchdog()




