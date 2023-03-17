import argparse
import curses
from typing import Any, List

def draw_menu(stdscr: "curses._CursesWindow", options: List[int], selected_option: int) -> None:
    """
    Draw the selectable options on the screen.

    Args:
        stdscr: A curses window object to draw on.
        options: A list of selectable options.
        selected_option: The currently selected option.

    Returns:
        None
    """
    # Clear the screen
    stdscr.clear()

    # Draw the menu
    stdscr.addstr("Select an option:\n")
    for option in options:
        if option == selected_option:
            stdscr.addstr("* ")
        else:
            stdscr.addstr("  ")
        stdscr.addstr(str(option) + "\n")

    # Refresh the screen
    stdscr.refresh()


def select_option(options: List[Any]) -> int:
    """
    Handle user input and return the selected option.

    Args:
        stdscr: A curses window object to draw on.
        options: A list of selectable options.

    Returns:
        The selected option.
    """
    stdscr = curses.initscr()
    
    # Turn off cursor blinking
    curses.curs_set(0)

    selected_option = options[0]
    index = options.index(selected_option)
    try:
        while True:
            # Draw the menu
            draw_menu(stdscr, options, selected_option)

            # Wait for user input
            key = stdscr.getch()

            # Move the selection up or down
            if key == 65:  # Up arrow key
                index = options.index(selected_option)
                selected_option = options[(index - 1) % len(options)]
            elif key == 66:  # Down arrow key
                index = options.index(selected_option)
                selected_option = options[(index + 1) % len(options)]
            elif key == ord('\n'):
                curses.endwin()
                return index
    except:
        curses.endwin()
    
    raise ValueError('An option was not selected')
    

def print_options(stdscr, options: List[str], selected: List[bool], current: int):
    stdscr.clear()
    for idx, (option, is_selected) in enumerate(zip(options, selected)):
        prefix = '[x]' if is_selected else '[ ]'
        highlight = curses.A_REVERSE if idx == current else curses.A_NORMAL
        stdscr.addstr(idx, 0, f'{prefix} {option}', highlight)
    stdscr.refresh()


def get_multiselect_input(stdscr, options: List[str]) -> List[bool]:
    curses.curs_set(0)
    current = 0
    selected = [False] * len(options)

    while True:
        print_options(stdscr, options, selected, current)
        key = stdscr.getch()

        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(options) - 1:
            current += 1
        elif key == ord(' '):  # Space key
            selected[current] = not selected[current]
        elif key == ord('\n'):  # Enter key
            break

    return selected



def select_multiple_options(options: List[str])-> List[bool]:
    """
    Prompt the user to select multiple options from a list using a curses-based interface.

    The user can navigate the list using arrow keys, select options using the space key,
    and confirm the selection with the Enter key.

    Args:
        options: A list of strings representing the options to choose from.

    Returns:
        A list of boolean values with the same length as the input list `options`.
                    Each boolean value indicates whether the corresponding option was selected
                    by the user (True) or not (False).
    """
    return curses.wrapper(get_multiselect_input, options)


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Select an option from a list')
    parser.add_argument('--multi', '-m',help="Test multi select command line", action='store_true')
    
    options = ['Option 1', 'Option 2', 'Option 3']
    
    args = parser.parse_args()

    if args.multi:
        selected_options = select_multiple_options(options)
        print('Raw selected option:', selected_options)
        print('Options selected:', [options[i] for i, selected in enumerate(selected_options) if selected])        
        
    else:
        selected_option = 0
        # Run the main function
        selected_option = select_option(options)
        # Do something with the selected option
        print('Options selected:', selected_option)
        if selected_option == 1:
            print('Option 1 selected')
        elif selected_option == 2:
            print('Option 2 selected')
        else:
            print('Option 3 selected')

    

