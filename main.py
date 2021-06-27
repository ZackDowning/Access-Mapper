from gui import gui_print, button, file_browse_botton, gui_print_box
import PySimpleGUI as Sg
from general import MgmtIPAddresses


if __name__ == '__main__':
    layout1 = [
        gui_print('Select file containing switch management IP addresses'),
        file_browse_botton('Browse'),
        button('Check File')
    ]
    window1 = Sg.Window('Access Mapper', layout1, margins=(100, 100))
    current_window = window1
    while True:
        event, values = current_window.read()
        if event == 'Check File' or event == 'Retry':
            try:
                Sg.user_settings_set_entry('-filename-', values['file'])
                mgmt_file = MgmtIPAddresses(values['file'])
                if mgmt_file.validate():
                    current_window.close()
                    layout2 = [
                        gui_print('Valid File')
                    ]
                    current_window = Sg.Window('Access Mapper', layout2, margins=(100, 100))
                else:
                    current_window.close()
                    invalid_lines = 'Line    | Value\n'
                    line_nums = mgmt_file.invalid_line_nums
                    ip_addresses = mgmt_file.invalid_ip_addresses
                    for (line_n, ip_addr) in zip(
                            line_nums, ip_addresses):
                        blank_space = ''
                        for num1 in range(0, 10 - len(line_n)):
                            blank_space += ' '
                        invalid_lines += f'{line_n}{blank_space}  {ip_addr}'
                    layout3 = [
                        gui_print('Invalid File Entries'),
                        gui_print_box(invalid_lines, size=(30, 15)),
                        gui_print('Select file containing switch management IP addresses'),
                        file_browse_botton('Browse'),
                        button('Retry')
                    ]
                    current_window = Sg.Window('Access Mapper', layout3, margins=(100, 100))
            except FileNotFoundError:
                current_window.close()
                layout3 = [
                    gui_print('File or directory not found.'),
                    gui_print('Select file containing switch management IP addresses'),
                    file_browse_botton('Browse'),
                    button('Retry')
                ]
                current_window = Sg.Window('Access Mapper', layout3, margins=(100, 100))
        if event == Sg.WIN_CLOSED:
            break

    current_window.close()
