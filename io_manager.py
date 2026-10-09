from questionnaire import full_survey #Questionnaire functionality
from user import user_login, user_register, change_username, change_password

#Print menu options
def menu_page(menu):
    print("\n---------MENU---------")
    for i, option in enumerate(menu.keys(), start=1):
        print(f"{i}. {option}")
    print("----------------------\n")
    while True:
        option = input(f"Enter option (1-{len(menu)}): ").strip()
        if option.isdigit() and 1 <= int(option) <= len(menu):
            return list(menu.keys())[int(option) - 1]
        else:
            print("Invalid option. Please select a valid option.")

#Main Program
def io_main():
    #I/O Files
    survey_file = "results.json"
    logic_file = "logic_sample.json"
    ai_file = "ai_sample.json"
    files = [survey_file,logic_file,ai_file]

    #Title
    print("============================")
    print("Welcome to Mental Health Tool")
    print("============================\n")

    #User menu options
    main_menu = {
        "Register New User": lambda: user_register(),
        "Login": lambda: user_login() ,
        "Exit": None
    }
    submenu = {      
        "Start Survey": lambda: full_survey(files),
        "View History": lambda: print("This functionality has not been implemented yet."),
        "Change Username": lambda: print("This functionality has not been implemented yet."),
        "Change Password": lambda: print("This functionality has not been implemented yet."),
        "Logout": lambda: None
    }

    loggedin = False

    #Main Menu
    while True:
        option = menu_page(main_menu)
        if option == "Exit":
            print("\nProgram terminated. Thank You!")
            return
        main_menu[option]()

        #Sub-Menu
        while True:
            option = menu_page(submenu)
            if option == "Logout":
                print("\nSuccessfully Logged Out.")
                break
            submenu[option]()
            input("\nPress Enter to return to the menu...")
    

#test
if __name__ == "__main__":
    io_main()