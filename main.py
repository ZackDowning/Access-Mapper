import subprocess
import time
from math import ceil
from gui import (
    w_main,
    w_file_not_found,
    w_invalid_file_entry,
    w_discovery_query,
    w_function_selection,
    w_invalid_discovery_query,
    w_finished_discovery,
    w_progress_bar
)
import PySimpleGUI as Sg
from general import MgmtIPAddresses, mac_address_formatter
from address_validator import ipv4, macaddress
from discovery import Discovery
from argparse import ArgumentParser
import sys

# PyInstaller bundle command:
# pyinstaller -w -F --hidden-import PySimpleGUI --add-data templates;templates main.py
# TODO: Add comments
# TODO: Find out how to kill threadpool
# TODO: Show progressbar update by phase
# TODO: Add menu to just find specific info about device
# TODO: Add VLAN change based on IP Address or MAC Address - device provisioning
#   TODO: Allow manual input of switch management IP and interface to change
#   TODO: Allow manual text input or selecting from dropdown

if __name__ == '__main__':
    # Parses argument to check length of progress bar for progress bar window subprocess
    parser = ArgumentParser()
    parser.add_argument('-l', dest='length')
    bar_length = parser.parse_args().length

    if bar_length is None:
        discovery_init = False
        discovery_finished = False
        input_type = None
        mgmt_file = None
        query_value = None
        username = None
        password = None
        d = None
        current_window = w_main()

        while True:
            event, values = current_window.read(timeout=10)
            if event == 'Check File' or event == 'Retry':
                try:
                    Sg.user_settings_set_entry('-filename-', values['file'])
                    mgmt_file = MgmtIPAddresses(values['file'])
                    if mgmt_file.validate:
                        current_window = w_function_selection(current_window)
                    else:
                        current_window = w_invalid_file_entry(current_window, mgmt_file)
                except FileNotFoundError:
                    current_window = w_file_not_found(current_window)
            if event == 'Main Page':
                input_type = None
                current_window = w_main(current_window)
            if event == 'Function Selection':
                input_type = None
                current_window = w_function_selection(current_window)
            if event == 'Endpoint Discovery':
                input_type = None
                current_window = w_discovery_query(current_window)
            if event == 'Run Discovery':
                Sg.user_settings_set_entry('-username-', values['user'])
                query_value = values[0]
                username = values['user']
                password = values['pass']
                if ipv4(query_value):
                    input_type = 'IP_Address'
                    discovery_init = True
                elif macaddress(query_value):
                    query_value = mac_address_formatter(query_value)
                    input_type = 'MAC_Address'
                    discovery_init = True
                else:
                    input_type = None
                    current_window = w_invalid_discovery_query(current_window)
            if discovery_init:
                if len(mgmt_file.mgmt_ips) > 50:
                    bar_length = int(ceil(len(mgmt_file.mgmt_ips) / 50) * 70)
                else:
                    bar_length = 80
                if getattr(sys, 'frozen', False):
                    main_file = 'access-mapper.exe'
                else:
                    main_file = 'python3 main.py'
                subprocess_run = subprocess.Popen(f'{main_file} -l {bar_length}', shell=True)
                current_window.close()
                start = time.perf_counter()
                d = Discovery(query_value, input_type, mgmt_file.mgmt_ips, username, password)
                end = time.perf_counter()
                # Used for debugging
                discovery_time = int(round(end - start, 0))

                discovery_init = False
                discovery_finished = True
                subprocess_run.terminate()
            if discovery_finished:
                discovery_finished = False
                current_window = w_finished_discovery(
                    current_window, d.host_mac_address, d.host_ip_address, d.gateway_ip_address,
                    d.gateway_hostname, d.gateway_mgmt_ip_address, d.host_vlan,
                    d.connected_device_interface, d.connected_device_hostname,
                    d.connected_device_mgmt_ip_address, d.subnet_mask, d.network)
            if event == Sg.WIN_CLOSED:
                break
        current_window.close()

    else:
        # PySimpleGUI Progressbar for subprocess
        bar_length = int(bar_length) * 4
        current_window = w_progress_bar(bar_length)
        bar_progress = 0
        for i in range(bar_length - 1):
            time.sleep(0.25)
            bar_progress += 1
            if i == bar_length - 2:
                event, values = current_window.read()
            else:
                event, values = current_window.read(timeout=10)
                current_window['-PROG-'].update(bar_progress)
            if event == Sg.WIN_CLOSED:
                break
