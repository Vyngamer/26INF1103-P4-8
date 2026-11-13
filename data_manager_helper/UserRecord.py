import uuid
'''
Represents a user account in the application
'''
class UserRecord:
    def __init__(self, username: str, password: str, user_id: str | None = None) -> None:

        #generate a new id for a new user, keep the existing ide when loading one
        if user_id is None:
            self.__user_id: str = str(uuid.uuid4())
        
        else:
            self.__user_id = user_id

        self.__username: str = username
        self.__password: str = password

    def get_user_id(self) -> str:
        return self.__user_id

    def get_username(self) -> str:
        return self.__username

    def get_password(self) -> str:
        return self.__password

    # return the account as a dict for saving into db
    def to_dict(self) -> dict[str, str]:
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "password": self.__password
        }