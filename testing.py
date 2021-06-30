from getpass import getpass
from gui import (
    gui_print, w_main, w_file_not_found, w_invalid_file_entry, button)
from discovery import MACAddress
from general import Connection, MgmtIPAddresses, MultiThread

import PySimpleGUI as Sg

if __name__ == '__main__':
    username = input('Username: ')
    password = getpass('Password: ')
    current_window = w_main()
    while True:
        event, values = current_window.read()
        if event == 'Check File':
            Sg.user_settings_set_entry('-filename-', values['file'])
            mgmt_file_location = values['file']



            while True:
                MultiThread()
        if event == Sg.WIN_CLOSED:
            break

    current_window.close()
