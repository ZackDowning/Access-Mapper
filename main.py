from gui import (
    w_main,
    w_file_not_found,
    w_invalid_file_entry,
    w_discovery_query,
    w_function_selection,
    w_invalid_discovery_query,
    w_finished_discovery
)
import PySimpleGUI as Sg
from general import MgmtIPAddresses
from address_validator import ipv4, macaddress
from discovery import Discovery

if __name__ == '__main__':
    current_window = w_main()
    discovery_init = False
    input_type = None
    mgmt_file = None
    query_value = None
    username = None
    password = None
    d = None
    while True:
        event, values = current_window.read()
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
            query_value = values[0]
            username = values[1]
            password = values[2]
            if ipv4(query_value):
                input_type = 'IP_Address'
                discovery_init = True
            elif macaddress(query_value):
                input_type = 'MAC_Address'
                discovery_init = True
            else:
                input_type = None
                current_window = w_invalid_discovery_query(current_window)
        if discovery_init:
            discovery_init = False
            d = Discovery(input_type, mgmt_file.mgmt_ips, query_value, username, password)
            current_window = w_finished_discovery(
                current_window, d.host_mac_address, d.host_ip_address, d.gateway_ip_address,
                d.gateway_hostname, d.gateway_mgmt_ip_address, d.host_vlan,
                d.connected_device_interface, d.connected_device_hostname,
                d.connected_device_mgmt_ip_address)
            current_window = current_window
        if event == Sg.WIN_CLOSED:
            break

    current_window.close()
