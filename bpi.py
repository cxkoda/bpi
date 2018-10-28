#!/usr/bin/env python3

from configobj import ConfigObj
import os, platform
import requests
import logging
import time

class bpi:
    def __init__(self, cfgFile):
        self.cfg = ConfigObj(cfgFile)
        self.__set_logger()
        self.__set_os_commands(platform.system())
        self.__set_check_type(self.cfg['bpi']['check_type'])

    def __set_logger(self):
        # create logger
        self.logger = logging.getLogger('bpi')
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(self.cfg['bpi']['log'])
        fh.setLevel(logging.INFO)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def __set_os_commands(self, os_name):
        '''
        sets some os specific commands
        '''
        if os_name == 'Linux':
            self.sys_ping = lambda adress: os.system('ping -c 1 -W 1 ' + adress + ' > /dev/null')
        elif os_name == 'Windows':
            self.sys_ping = lambda adress: os.system('PING ' + adress + ' -n 1 -w 1000 > NUL')
        else:
            logging.error('OS not detected: ' + os_name + ' - falling back on linux')
            self.__set_os_commands('Linux')

    def __set_check_type(self, check_type):
        '''
        sets the connection check type
        '''
        if check_type == 'internal':
            self.check_connection = self.check_connection_internal
        elif check_type == 'external':
            self.check_connection = self.check_connection_external
        else:
            logging.error('check_type not defined: ' + check_type + ' - falling back on external')
            self.__set_check_type('external')

    def check_connection_external(self):
        '''
        Checks if an internet connection can be established, i.e. if a ping is successful
        preformance: 0.06s (authorized), 0.6s (not authorized)
        :return: bool: connection established
        '''

        if self.sys_ping(self.cfg['bpi']['ping_adress']) == 0:
            self.state = 'AUTHORIZED'
        else:
            self.state = 'NOT_AUTHORIZED'

        return self.state == 'AUTHORIZED'

    def check_connection_internal(self):
        '''
        Checks if an internet connection can be established, i.e. if the plug-inn client is authorized
        preformance: 0.06s (authorized), 0.06s (not authorized)
        :return: bool: connection established
        '''

        response = requests.get(self.cfg['plug-inn']['host'] + '/api/captiveportal/access/status/0/')
        self.status = response.json()
        self.state = self.status['clientState']

        return self.state == 'AUTHORIZED'

    def send_credentials(self):
        '''
        Send the credentials to the pluginn portal
        :return: bool: transmission success
        '''
        try:
            requests.post(self.cfg['plug-inn']['host'] + '/api/captiveportal/access/logon/0/',
                          data={
                              'user': self.cfg['plug-inn']['username'],
                              'password': self.cfg['plug-inn']['password']
                          })
            self.logger.info('plug-inn credentials have been sent')
            return True
        except requests.RequestException:
            self.logger.error('Unexpected Transmission Error!')
            return False

    def start_watchdog(self):
        '''
        Start a predefined watchdog
        '''
        self.logger.info('Watchdog started')
        has_connection = self.check_connection_external()
        had_connection = has_connection
        while True:
            has_connection = self.check_connection_external()
            if has_connection and not had_connection:
                self.logger.info('Reconnected')
            if not has_connection and had_connection:
                self.logger.info('Disconnected')

            had_connection = has_connection
            if not has_connection:
                self.send_credentials()

            time.sleep(int(self.cfg['bpi']['sleep_time']))


if __name__ == '__main__':
    bpi_handler = bpi('bpi.ini')
    bpi_handler.start_watchdog()




