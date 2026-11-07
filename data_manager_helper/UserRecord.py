import uuid

# Represents a user account in the application
class UserRecord:
    def __init__(self, username, password, user_id=None):
        
        if user_id is None:
            self.__user_id = str(uuid.uuid4())
        
        else:
            self.__user_id = user_id

        self.__username = username
        self.__password = password

    def get_user_id(self):
        return self.__user_id

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

    def to_dict(self):
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "password": self.__password
        }