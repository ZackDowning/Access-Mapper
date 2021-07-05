import os
import sys
from concurrent.futures import ThreadPoolExecutor, wait
from netmiko import ConnectHandler, ssh_exception, SSHDetect
from address_validator import ipv4
from icmplib import ping

if getattr(sys, 'frozen', False):
    os.environ['NET_TEXTFSM'] = sys._MEIPASS
else:
    os.environ['NET_TEXTFSM'] = './templates'


def mac_address_formatter(mac_address):
    if '.' not in mac_address:
        x = mac_address.replace(':', '').replace('-', '')
        return f'{x[0:4]}.{x[4:8]}.{x[8:12]}'
    else:
        return mac_address


class MgmtIPAddresses:
    """Input .txt file location containing list of management IP addresses"""
    def __init__(self, mgmt_file_location):
        self.mgmt_file_location = mgmt_file_location
        self.mgmt_ips = []
        self.invalid_line_nums = []
        self.invalid_ip_addresses = []
        self.validate = False
        invalid_lines = 0
        with open(self.mgmt_file_location) as file:
            for idx, address in enumerate(file):
                ip_address = str(address).strip('\n')
                if ipv4(ip_address) is False:
                    self.invalid_line_nums.append(str(idx + 1))
                    self.invalid_ip_addresses.append(str(address))
                    invalid_lines += 1
                else:
                    self.mgmt_ips.append(ip_address)
            if invalid_lines == 0:
                self.validate = True


def reachability(ip_address):
    """Returns bool if host is reachable"""
    return ping(ip_address, privileged=False, count=4).is_alive


class Connection:
    """SSH or TELNET Connection Initiator"""
    def __init__(self, ip_address, username, password, devicetype='autodetect', con_type=None):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.hostname = ''
        self.devicetype = devicetype
        self.con_type = con_type
        self.exception = 'None'
        self.authentication = False
        self.authorization = False
        self.connectivity = False
        self.session = None
        self.device = {
            'device_type': self.devicetype,
            'ip': ip_address,
            'username': username,
            'password': password
        }

    def check(self):
        if reachability(self.ip_address):
            try:
                try:
                    autodetect = SSHDetect(**self.device).autodetect()
                    self.device['device_type'] = autodetect
                    self.devicetype = autodetect
                    self.session = ConnectHandler(**self.device)
                except ValueError:
                    try:
                        self.device['device_type'] = 'cisco_ios'
                        self.devicetype = 'cisco_ios'
                        self.session = ConnectHandler(**self.device)
                    except ValueError:
                        self.device['device_type'] = 'cisco_ios'
                        self.devicetype = 'cisco_ios'
                        self.session = ConnectHandler(**self.device)
                showver = self.session.send_command('show version', use_textfsm=True)
                if not showver.__contains__('Failed'):
                    self.hostname = showver[0]['hostname']
                    self.authorization = True
                self.authentication = True
                self.connectivity = True
                self.con_type = 'SSH'
            except (ConnectionRefusedError, ValueError, ssh_exception.NetmikoAuthenticationException,
                    ssh_exception.NetmikoTimeoutException):
                try:
                    try:
                        self.device['device_type'] = 'cisco_ios_telnet'
                        self.devicetype = 'cisco_ios_telnet'
                        self.device['secret'] = self.password
                        self.session = ConnectHandler(**self.device)
                        showver = self.session.send_command('show version', use_textfsm=True)
                        if not showver.__contains__('Failed'):
                            self.hostname = showver[0]['hostname']
                            self.authorization = True
                        self.authentication = True
                        self.connectivity = True
                        self.con_type = 'TELNET'
                    except ssh_exception.NetmikoAuthenticationException:
                        self.device['device_type'] = 'cisco_ios_telnet'
                        self.devicetype = 'cisco_ios_telnet'
                        self.device['secret'] = self.password
                        self.session = ConnectHandler(**self.device)
                        showver = self.session.send_command('show version', use_textfsm=True)
                        if not showver.__contains__('Failed'):
                            self.hostname = showver[0]['hostname']
                            self.authorization = True
                        self.authentication = True
                        self.connectivity = True
                        self.con_type = 'TELNET'
                except ssh_exception.NetmikoAuthenticationException:
                    self.connectivity = True
                    self.exception = 'NetmikoAuthenticationException'
                except ssh_exception.NetmikoTimeoutException:
                    self.exception = 'NetmikoTimeoutException'
                except ConnectionRefusedError:
                    self.exception = 'ConnectionRefusedError'
                except ValueError:
                    self.exception = 'ValueError'
                except TimeoutError:
                    self.exception = 'TimeoutError'
            except OSError:
                self.exception = 'OSError'
            if self.session is not None:
                self.session.disconnect()
        else:
            self.exception = 'NoPingEcho'
        return self

    def connection(self):
        if reachability(self.ip_address):
            try:
                if self.con_type == 'TELNET':
                    self.device['secret'] = self.password
                    self.session = ConnectHandler(**self.device)
                else:
                    self.session = ConnectHandler(**self.device)
            except ConnectionRefusedError:
                self.exception = 'ConnectionRefusedError'
            except ssh_exception.NetmikoAuthenticationException:
                self.exception = 'NetmikoAuthenticationException'
            except ssh_exception.NetmikoTimeoutException:
                self.exception = 'NetmikoTimeoutException'
            except ValueError:
                self.exception = 'ValueError'
            except TimeoutError:
                self.exception = 'TimeoutError'
            except OSError:
                self.exception = 'OSError'
        else:
            self.exception = 'NoPingEcho'
        return self


class MultiThread:
    """Multithread Initiator"""
    def __init__(self, function=None, iterable=None, successful_devices=None, failed_devices=None, threads=50):
        self.successful_devices = successful_devices
        self.failed_devices = failed_devices
        self.iterable = iterable
        self.threads = threads
        self.function = function

    """Executes multithreading on provided function and iterable"""
    def mt(self):
        executor = ThreadPoolExecutor(self.threads)
        futures = [executor.submit(self.function, val) for val in self.iterable]
        wait(futures, timeout=None)
        return self

    """Returns bool if Windows PyInstaller bug is present with provided lists for successful and failed devices"""
    def bug(self):
        successful = len(self.successful_devices)
        failed = len(self.failed_devices)
        if (successful + failed) == len(self.iterable):
            return False
        else:
            return True
