from typing import Protocol, TypeVar, Sequence
from dataclasses import dataclass, field
from typing import Optional
import os, json

T = TypeVar('T')

@dataclass
class User:
    id: int
    name: str
    login: str
    password: str
    email: Optional[str] = field(default=False, compare=False)
    address: Optional[str] = field(default=False, compare=False)

    def __mt__(self, other) -> bool:
        return self.name.lower() > other.name.lower()

    def __lt__(self, other) -> bool:
        return self.name.lower() < other.name.lower()

#region Protocols
class DataRepositoryProtocol(Protocol[T]): #CRUD
    def get_all(self) -> Sequence[T]:
        ...
    def get_by_id(self, id: int) -> Optional[T]:
        ...
    def add(self, item: T) -> None:
        ...
    def update(self, item:T ) -> None:
        ...
    def delete(self, item: T) -> None:
        ...

class UserRepositoryProtocol(DataRepositoryProtocol[User], Protocol):
    def get_by_login(self, login: str) -> Optional[User]:
        ...

class AuthServiceProtocol(Protocol):
    def sign_in(user: User) -> bool:
        ...
    def sign_out(user: User) -> None:
        ...
    @property
    def is_authorized(user: User) -> bool:
        ...
    @property
    def current_user(user: User) -> Optional[User]:
        ...
#endregion

class DataRepository(DataRepositoryProtocol[T]):
    def __init__(self, file_path: str, T: type) -> None:
        try:
            with open(file_path, 'r') as file:
                pass
            self.file_path = file_path
            self._data = self.load_json()
            self.T = T
        except FileNotFoundError:
            print("ERROR: File not found!")
        except PermissionError:
            print("ERROR: Permission denied!")
        except IOError as e:
            print(f"ERROR: {e}")

    def load_json(self) -> None:
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("ERROR: File not found!")
        except PermissionError:
            print("ERROR: Permission denied!")
        except IOError as e:
            print(f"ERROR: {e}")

    def save_json(self) -> None:
        try:
            with open(self.file_path, 'w') as file:
                json.dump(self._data, file, indent=2)
        except FileNotFoundError:
            print("ERROR: File not found!")
        except PermissionError:
            print("ERROR: Permission denied!")
        except IOError as e:
            print(f"ERROR: {e}")

    def get_all(self) -> Sequence[T]:
        return [self.T(**item) for item in self.load_json()]

    def get_by_id(self, id: int) -> Optional[T]:
        for item in self.load_json():
            if item['id'] == id:
                return self.T(**item)
        return None

    def add_by_list(self, items: list) -> None:
        for i in items:
            if not self.get_by_id(i.id):
                self.sign_up(i)

    def sign_up(self, item: T) -> None:
        if self.get_by_id(item.id):
            return
        self._data.append(item.__dict__)
        self.save_json()

    def update(self, item: T) -> None:
        for i, entry in enumerate(self._data):
            if entry['id'] == item.id:
                self._data[i] = item.__dict__
                break
        self.save_json()

    def delete(self, item: T) -> None:
        self._data = [elem for elem in self._data if elem[id] != item.id]
        self.save_json(self._data)

    def show_data(self) -> None:
        for item in self._data:
            print(item)

class UserRepository(DataRepository[User], UserRepositoryProtocol):
    def __init__(self, file_path: str) -> None:
        DataRepository.__init__(self, file_path = file_path, T=User)

    def get_by_login(self, login: str) -> Optional[User]:
        for item in self.load_json():
            if item["login"] == login:
                return User(**item)
        return None

class AuthService(AuthServiceProtocol):
    def __init__(self, user_repo: UserRepositoryProtocol, session_file: str) -> None:
        self.session_file = session_file
        self.user_repo = user_repo
        self._current_user: Optional[User] = None
        self.start_session()

    def start_session(self) -> None:
        try:
            with open(self.session_file, 'r') as f:
                session = json.load(f)
                self._current_user = self.user_repo.get_by_id(session['user_id'])
        except FileNotFoundError:
            self._current_user = None

    def end_session(self) -> None:
        if not self._current_user:
            return
        try:
            with open(self.session_file, 'w') as file:
                json.dump({'user_id': self._current_user.id}, file)
        except FileNotFoundError as e:
            print(e)

    def sign_in(self, login: str, password: str) -> bool:
        user = self.user_repo.get_by_login(login)
        if user and user.password == password:
            self._current_user = user
            self.end_session()
            return True
        return False

    def sign_out(self) -> None:
        if self.is_authorized:
            self._current_user = None
            try:
                os.remove(self.session_file)
            except FileNotFoundError as e:
                print(e)

    @property
    def is_authorized(self) -> bool:
        return self._current_user != None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

#actual code
users = [
    User(id=0, name="Matthew Shtogrin", login="JankFank", password="qwerty12345", email="iam@jankfank.ru"),
    User(id=1, name="Mikhail Vereshagin", login="Boss", password="bfu4life")]

user_data = UserRepository(file_path='users_data.json')
session_info = AuthService(user_data, session_file='session_data.json')

user_data.add_by_list(users)

#Добавление пользователя
print("Данные до добавления")
user_data.show_data()
sign_up = User(id=2, name="John Doe" ,login="JD", password="examplepass")
user_data.sign_up(sign_up)
print()
print("Данные после добавления")
user_data.show_data()

#Редактирование свойств пользователя
print("\n")
example_user = user_data.get_by_login("JD")
print("Данные до обновления")
print(example_user)
example_user.name = "JohnPork"
example_user.password = "amacallinbruh"
user_data.update(example_user)
print("Данные после обновления")
print(user_data.get_by_login("JD"))

#Авторизация
print("\n")
session_info.sign_out()
print(f"Залогинен ли кто-то в текущей сессии?: {session_info.is_authorized}")
while session_info.is_authorized!=True:
    login_test, password_test = str(input("Введите (ЛОГИН:ПАРОЛЬ): ")).split(":")
    session_info.sign_in(login_test, password_test)
    print(f"Залогинен ли кто-то в текущей сессии?: {session_info.is_authorized}")

#Смена текущего пользователя
print("\n")
print(f"Аккаунт сессии: {session_info.current_user}")
print("Разлогин*")
session_info.sign_out()
print(f"Аккаунт сессии: {session_info.current_user}")
print("Логин*")
session_info.sign_in("Boss", "bfu4life")
print(f"Аккаунт сессии: {session_info.current_user}")


