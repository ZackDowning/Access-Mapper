import PySimpleGUI as Sg


def test():
    Sg.theme('Dark Red')

    BAR_MAX = 1000

    # layout the Window
    layout = [[Sg.Text('A custom progress meter')],
              [Sg.ProgressBar(BAR_MAX, orientation='h', size=(20, 20), key='-PROG-')],
              [Sg.Cancel()]]

    # create the Window
    window = Sg.Window('Custom Progress Meter', layout, modal=True)
    # loop that would normally do something useful
    for i in range(1000):
        # check to see if the cancel button was clicked and exit loop if clicked
        event, values = window.read(timeout=10)
        if event == 'Cancel' or event == Sg.WIN_CLOSED:
            break
            # update bar with loop value +1 so that bar eventually reaches the maximum
        window['-PROG-'].update(i + 1)
    # done with loop... need to destroy the window as it's still open
    window.close()
