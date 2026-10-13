'''
User Account Actions
'''

import json
import os
import uuid
from hasher import hash_password, verify_password, needs_upgrade
from prompts import prompt_text, prompt_password

DATABASE = "users.json"
MIN_PASSWORD_LENGTH = 4

'''
Helpers
'''

#Build the dictionary every account action returns
def make_result(ok, message, **data):
    result = {"ok": ok, "message": message}
    result.update(data)
    return result

#Load users list. [] if the file doesn't exist yet, None if corrupted
def load_users():
    if not os.path.exists(DATABASE):
        return []
    try:
        with open(DATABASE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return None

#Save users list (write to a temp file first for program crash handling)
def save_users(users_list):
    temp_file = DATABASE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(users_list, file, indent=4)
    os.replace(temp_file, DATABASE)   

#Find a user by username (None if not found)
def find_user(users_list, username):
    for user in users_list:
        if user["username"] == username:
            return user
    return None

#Find a user by id (None if not found)
def find_user_by_id(users_list, uid):
    for user in users_list:
        if user["user_id"] == uid:
            return user
    return None

#Password validation
def pw_validation(password):
    problems = []
    #Check for minimum length
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"at least {MIN_PASSWORD_LENGTH} characters")
    #Check for no spaces
    if password != password.strip():
        problems.append("no spaces at the start or end")
    #Check for at least one number
    if not any(char.isdigit() for char in password):
        problems.append("at least one number")
    #Check for at least one special character
    if not any(not char.isalnum() and not char.isspace() for char in password):
        problems.append("at least one special character (e.g. ! @ # $ %)")
    return problems

#Ask for a new password twice. Success result carries the password in "password"
def prompt_new_password(noun="Password"):
    print(f"Password must:\n1. Be at least {MIN_PASSWORD_LENGTH} characters long\n2. Contain at least one number & one special character (e.g. ! @ # $ %)\n3. Have no spaces at the start or end")
    password = prompt_password(f"Please Enter A {noun}: ")
    problems = pw_validation(password)
    if problems:
        return make_result(False, "Password must have: " + ", ".join(problems) + ".")
    confirm_password = prompt_password(f"Please Re-enter The {noun}: ")
    if password != confirm_password:
        return make_result(False, "Passwords do not match, please try again.")
    return make_result(True, "", password=password)

'''
User Actions
'''

#Register New User
def user_register():
    users_list = load_users()
    if users_list is None:
        return make_result(False, "User database is corrupted. Please check users.json.")

    print("Create a new user")
    username = prompt_text("Please Enter A Username: ")
    if find_user(users_list, username):
        return make_result(False, "Username already exists, please try again.")

    new_password = prompt_new_password()
    if not new_password["ok"]:
        return new_password

    new_user = {
        "user_id": str(uuid.uuid4()),
        "username": username,
        "password": hash_password(new_password["password"])
    }
    users_list.append(new_user)
    save_users(users_list)
    return make_result(True, "Account created successfully!",
                       uid=new_user["user_id"], username=username)

#Login Existing User
def user_login():
    users_list = load_users()
    if users_list is None:
        return make_result(False, "User database is corrupted. Please check users.json.")
    if not users_list:
        return make_result(False, "No users registered yet. Please register first.")

    username = prompt_text("Please Enter Your Username: ")
    password = prompt_password("Please Enter Your Password: ")

    user = find_user(users_list, username)
    if user is None or not verify_password(password, user["password"]):
        return make_result(False, "Invalid username or password.")

    #Silently upgrade old unsalted hashes now that we have the plain password
    if needs_upgrade(user["password"]):
        user["password"] = hash_password(password)
        save_users(users_list)

    return make_result(True, f"Login successful! Welcome, {user['username']}!",
                       uid=user["user_id"], username=user["username"])

#Change Username
def change_username(uid):
    users_list = load_users()
    if users_list is None:
        return make_result(False, "User database is corrupted. Please check users.json.")
    user = find_user_by_id(users_list, uid)
    if user is None:
        return make_result(False, "Current user not found.")

    new_username = prompt_text("Enter your new username: ")
    if find_user(users_list, new_username):
        return make_result(False, "Username already exists, please try again.")

    user["username"] = new_username
    save_users(users_list)
    return make_result(True, "Username updated successfully!", username=new_username)

#Change Password
def change_password(uid):
    users_list = load_users()
    if users_list is None:
        return make_result(False, "User database is corrupted. Please check users.json.")
    user = find_user_by_id(users_list, uid)
    if user is None:
        return make_result(False, "Current user not found.")

    current_password = prompt_password("Please Enter Your Current Password: ")
    if not verify_password(current_password, user["password"]):
        return make_result(False, "Incorrect current password. Please try again.")

    new_password = prompt_new_password("New Password")
    if not new_password["ok"]:
        return new_password

    user["password"] = hash_password(new_password["password"])
    save_users(users_list)
    return make_result(True, "Password updated successfully!")