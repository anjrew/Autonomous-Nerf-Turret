# from typing import List
# from select_option import draw_menu, main
# import curses
# from pytest_mock import MockerFixture

# class MockCursesWindow:
#     def clear(self) -> None:
#         pass

#     def addstr(self, text: str) -> None:
#         pass

#     def refresh(self) -> None:
#         pass

#     def getch(self) -> int:
#         return 1


# class MockCurses:
#     KEY_UP: int = curses.KEY_UP
#     KEY_DOWN: int = curses.KEY_DOWN

#     @staticmethod
#     def initscr() -> MockCursesWindow:
#         return MockCursesWindow()

#     @staticmethod
#     def curs_set(visibility: int) -> None:
#         pass
    
#     @staticmethod
#     def endwin() -> None:
#         pass



# def test_draw_menu(mocker: MockerFixture) -> None:
#     """
#     Test that the draw_menu function draws the menu correctly on the screen.
#     """
#     mocker.patch("select_option.curses", MockCurses)
#     stdscr = mocker.MagicMock(spec=MockCursesWindow)
#     # Rest of the test function code...  
    
#     options: List[int] = [1, 2, 3]

#     draw_menu(stdscr, options, 2)
#     stdscr.clear.assert_called_once()
#     stdscr.addstr.assert_has_calls([
#         mocker.call("Select an option:\n"),
#         mocker.call("  1\n"),
#         mocker.call("* 2\n"),
#         mocker.call("  3\n"),
#     ])
#     stdscr.refresh.assert_called_once()


# def test_main_up_down_select(mocker: MockerFixture) -> None:
#     """
#     Test that the main function selects the correct option with up/down arrow keys and return key.
#     """
#     mocker.patch("select_option.curses", MockCurses)
#     stdscr = mocker.MagicMock(spec=MockCursesWindow)
#     options: List[int] = [1, 2, 3]

#     # Mock user input
#     stdscr.getch.side_effect = [curses.KEY_DOWN, ord('\n')]

#     # Run the main function
#     selected_option = main(stdscr, options)

#     # Assert that the correct option was selected
#     assert selected_option == 2


# def test_main_wraparound(mocker: MockerFixture) -> None:
#     """
#     Test that the main function wraps around the options list when arrow keys are used.
#     """
#     mocker.patch("select_option.curses", MockCurses)
#     stdscr = mocker.MagicMock(spec=MockCursesWindow)
#     options: List[int] = [1, 2, 3]

#     # Mock user input
#     stdscr.getch.side_effect = [
#         curses.KEY_UP,
#         curses.KEY_UP,
#         curses.KEY_UP,
#         curses.KEY_DOWN,
#         ord('\n'),
#     ]

#     # Run the main function
#     selected_option = main(stdscr, options)

#     # Assert that the correct option was selected
#     assert selected_option == 3


# def test_main_invalid_input(mocker: MockerFixture) -> None:
#     """
#     Test that the main function selects the first option by default when invalid input is provided.
#     """
#     mocker.patch("select_option.curses", MockCurses)
#     stdscr = mocker.MagicMock(spec=MockCursesWindow)
#     options: List[int] = [1, 2, 3]

#     # Mock user input
#     stdscr.getch.side_effect = [ord('a'), ord('b'), ord('c'), ord('\n')]

#     # Run the main function
#     selected_option = main(stdscr, options)

#     # Assert that the first option was selected by default
#     assert selected_option == options[0]
