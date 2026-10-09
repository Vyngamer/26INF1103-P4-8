import json
import os
import uuid
import pwinput
from hasher import hash_password

DATABASE = "users.json" 

#Password validation
def pw_validation():
    pass

#Register New User
def user_register():
    if os.path.exists(DATABASE):
        with open(DATABASE, 'r') as json_file:
            try:
                users_list = json.load(json_file)
            except json.JSONDecodeError:
                users_list = []
    else:
        users_list = []

    print("Create a new user")
    while True:
        # have length limit for userrname
        username = input("Please Enter A Username: ")
        if not username:
            print("Username cannot be empty. Please try again.")
            continue
        break

    #Check if username already exists
    for user in users_list:
        if user["username"] == username:
            print("Username already exists, please try again")
            return "username_exists" 
            # The 'return' stops the function immediately, so we don't need 'username_pass'

    #Prompt user to enter password

    # password cannot have space at the front and back
    #Disallowed characters for password
    forbidden = []

    while True:
        password = pwinput.pwinput(prompt="Please Enter A Password: ")
        if not password:
            print("Password cannot be empty. Please try again.")
            continue
        break

    while True:
        confirm_password = pwinput.pwinput(prompt="Please Re-enter A Password: ")
        if not confirm_password:
            print("Password confirmation cannot be empty. Please try again.")
            continue
        break

    if password != confirm_password:
        print("Passwords do not match, please try again")
        return "passwords_not_match"

    #Create new user to add to DB
    new_user = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "password": hash_password(password)
        #"history": []
    }

    #Add to DB
    users_list.append(new_user)
    
    with open(DATABASE, "w") as file:
        json.dump(users_list, file, indent=4)

    print("Account created successfully!")
    return "success"

#Login Existing User
def user_login():
    DATABASE = "users.json"  # Removed the forward slash so it saves in your current folder

    if not os.path.exists(DATABASE):
        print("No users registered yet. Please register first.")
        return "no_users"
    with open(DATABASE, 'r') as json_file:
        try:
            users_list = json.load(json_file)
        except json.JSONDecodeError:
            print("User database is corrupted. Please register again.")
            return "corrupted_database"
    while True:
        username = input("Please Enter Your Username: ").strip()
        if not username:
            print("Username cannot be empty. Please try again.")
            continue
        break

    while True:
        password = pwinput.pwinput(prompt="Please Enter Your Password: ").strip()
        if not password:
            print("Password cannot be empty. Please try again.")
            continue
        break
    hashed_password = hash_password(password)

    for user in users_list:
        if user["username"] == username and user["password"] == hashed_password:
            print(f"\nLogin successful! Welcome, {user["username"]}!")
            return user["username"]  # Return the username of the logged-in user

    print("Invalid username or password. Please try again.")
    return "invalid_credentials"

#Change Username
def change_username(current_username):
    # Load the existing users from the JSON file
    with open("users.json", "r") as file:
        users_list = json.load(file)

    # Find the user with the current username
    for user in users_list:
        if user["username"] == current_username:
            while True:
                new_username = input("Enter your new username: ").strip()
                if not new_username:
                    print("Username cannot be empty. Please try again.")
                    continue
                break
            # Check if the new username already exists
            for existing_user in users_list:
                if existing_user["username"] == new_username:
                    print("Username already exists, please try again.")
                    return "username_exists"

            # Update the username
            user["username"] = new_username

            # Save the updated users list back to the JSON file
            with open("users.json", "w") as file:
                json.dump(users_list, file, indent=4)

            print("Username updated successfully!")
            return new_username

    print("Current username not found.")
    return "username_not_found"

#Change Password
def change_password(username):
    if os.path.exists("users.json"):
        with open("users.json", 'r') as json_file:
            try:
                users_list = json.load(json_file)
            except json.JSONDecodeError:
                print("Database is corrupted. Please contact support.")
                return "corrupted_database"
    else:
        print("No users found. Please register first.")
        return "no_users"

    # Find the user in the list
    user_found = False
    for user in users_list:
        if user["username"] == username:
            user_found = True
            break

    if not user_found:
        print("User not found. Please register first.")
        return "user_not_found"

    # get the user to enter their current password
    current_password = pwinput.pwinput(prompt="Please Enter Your Current Password: ").strip()
    while True:
        if not current_password:
            print("Password cannot be empty. Please try again.")
            current_password = pwinput.pwinput(prompt="Please Enter Your Current Password: ").strip()
            continue
        break

    if hash_password(current_password) != user["password"]:
        print("Incorrect current password. Please try again.")
        return "incorrect_current_password"
    else:
        print("Current password verified. You can now set a new password.")
        while True:
            new_password = pwinput.pwinput(prompt="Please Enter A New Password: ").strip()
            if not new_password:
                print("New password cannot be empty. Please try again.")
                continue
            break
        while True:
            confirm_password = pwinput.pwinput(prompt="Please Re-enter The New Password: ").strip()
            if not confirm_password:
                print("Password confirmation cannot be empty. Please try again.")
                continue
            break
    
    if new_password != confirm_password:
        print("Passwords do not match, please try again")
        return "passwords_not_match"

    # Get the new password from the user
    # Update the user's password
    if new_password == confirm_password:
        for user in users_list:
            if user["username"] == username:
                user["password"] = hash_password(new_password)
                break

    # Save the updated users list back to the JSON file
    with open("users.json", "w") as file:
        json.dump(users_list, file, indent=4)

    print("Password updated successfully!")
    return "success"