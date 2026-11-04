'''
Common console output helpers (centred titles, errors, notices, pauses)
'''

class Console:
    DEFAULT_WIDTH = 50    # Default Width for text blocks

    # print title
    @staticmethod
    def title(title, length=DEFAULT_WIDTH):
        start = (length//2) - (len(title)//2) #Finds where to start title text in order to center it
        print("\n" + "="*length)
        print(" "*start + title)
        print("="*length)

    # moved from io_manager.print_error
    @staticmethod
    def error(msg):
        print("\nERROR: " + msg)

    # moved from io_manager.print_notice
    @staticmethod
    def notice(msg):
        print("\nNOTICE: " + msg)

    # moved from io_manager.print_welcome
    @staticmethod
    def welcome(msg):
        print("\n---" + msg + "---")

    # moved from io_manager.print_termination_msg
    @staticmethod
    def termination_msg():
        print("\n\nProgram terminated. Thank You!")

    # moved from io_manager.pause
    @staticmethod
    def pause():
        input("\nPress Enter to return to the menu...")