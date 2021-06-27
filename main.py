from gui import (
    gui_print, w_main, w_file_not_found, w_invalid_file_entry, button)
import PySimpleGUI as Sg
from general import MgmtIPAddresses


if __name__ == '__main__':
    current_window = w_main()
    while True:
        event, values = current_window.read()
        if event == 'Main Page':
            current_window = w_main(current_window)
        if event == 'Check File' or event == 'Retry':
            try:
                Sg.user_settings_set_entry('-filename-', values['file'])
                mgmt_file = MgmtIPAddresses(values['file'])
                if mgmt_file.validate():
                    current_window.close()
                    layout2 = [
                        gui_print('Valid File'),
                        button('Main Page')
                    ]
                    current_window = Sg.Window('Access Mapper', layout2, margins=(100, 100))
                else:
                    current_window = w_invalid_file_entry(current_window, mgmt_file)
            except FileNotFoundError:
                current_window = w_file_not_found(current_window)
        if event == Sg.WIN_CLOSED:
            break

    current_window.close()
