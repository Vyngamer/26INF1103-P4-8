from data_manager_helper.UserRecord import UserRecord
from data_manager_helper.StorageInterface import StorageInterface

'''
Keeps an in-memory list of user accounts.
'''

class UserManager:

    def __init__(self, storage: StorageInterface) -> None:
        self.__storage: StorageInterface = storage
        self.__users: list[UserRecord] = []

        self.load_users()

    # load all users from storage
    def load_users(self) -> list[UserRecord]:
        self.__users = []
        documents = self.__storage.load()
        self.__users = []

        for document in documents:
            user = UserRecord(
                username=document["username"],
                password=document["password"],
                user_id=document["user_id"]
            )

            self.__users.append(user)

        return self.get_users()

    def get_users(self) -> list[UserRecord]:
        return self.__users.copy()

    # create and save a new user
    def create_user(self, username: str, password: str) -> str | None:
        user = UserRecord(username, password)

        result = self.__storage.save(user.to_dict())

        if result is not None:
            self.__users.append(user)
            return user.get_user_id()

        return None

    # get user id
    def get_user_by_id(self, user_id: str) -> UserRecord | None:
        for user in self.__users:

            if user.get_user_id() == user_id:
                return user

        return None

    #get username
    def get_user_by_username(self, username: str) -> UserRecord | None:
        for user in self.__users:

            if user.get_username() == username:
                return user

        return None

    # update username or password of user
    def update_user(self, user_id: str, updates: dict[str, str]) -> bool:
        allowed_fields = {"username", "password"}

        if not isinstance(updates, dict):
            return False

        if not updates or not set(updates.keys()).issubset(allowed_fields):
            return False

        result = self.__storage.update(
            {"user_id": user_id},
            updates
        )

        if result:

            user = self.get_user_by_id(user_id)

            if user:

                current_data = user.to_dict()
                current_data.update(updates)

                updated_user = UserRecord(
                    username=current_data["username"],
                    password=current_data["password"],
                    user_id=user_id
                )

                self.__users.remove(user)
                self.__users.append(updated_user)

            return True

        return False

    # delete the user
    def delete_user(self, user_id: str) -> bool:  
        result = self.__storage.delete({"user_id": user_id})

        if result:

            self.__users = [
                user for user in self.__users
                if user.get_user_id() != user_id
            ]

            return True

        return False