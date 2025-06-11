from typing import Protocol, Any
import datetime

#region Protocols
class PropertyChangedListenerProtocol(Protocol):
    def on_property_changed(self, obj: Any, property_name: str) -> None:
        ...

class PropertyChangingListenerProtocol(Protocol):
    def on_property_changing(self, obj: Any, property_name: str, old_value: Any, new_value: Any) -> bool:
        ...

class DataChangedProtocol(Protocol):
    def add_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        ...
    def remove_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        ...

class DataChangingProtocol(Protocol):
    def add_property_changing_listener(self, listener: PropertyChangingListenerProtocol) -> None:
        ...
    def remove_property_changing_listener(self, listener: PropertyChangingListenerProtocol) -> None:
        ...
#endregion

#region Validators
class TitleValidator(PropertyChangingListenerProtocol):
    def on_property_changing(self, obj: DataChangingProtocol, property_name: str, old_value: Any, new_value: Any) -> bool:
        if property_name != 'title':
            return True
        if not isinstance(new_value, str):
            print("ERROR: Title is not str")
            return False
        if len(new_value) == 0:
            print("ERROR: No valid title")
            return False
        if old_value == new_value:
            print("ATTENTION: Title was changed to the same value")
            return True
        return True


class YearValidator(PropertyChangingListenerProtocol):
    def on_property_changing(self, obj: DataChangingProtocol, property_name: str, old_value: Any, new_value: Any) -> bool:
        if property_name != 'year':
            return True
        if not isinstance(new_value, int):
            print("ERROR: Year is not int")
            return False
        if new_value<1896:
            print("ERROR: First film was released in 1896! Do not try to trick me)")
            return False
        if new_value > datetime.datetime.now().year:
            print("ERROR: Film was not released yet")
            return False
        if old_value == new_value:
            print("ATTENTION: Year was changed to the same value")
            return True
        return True

class RatingValidator(PropertyChangingListenerProtocol):
    def on_property_changing(self, obj: DataChangingProtocol, property_name: str, old_value: Any, new_value: Any) -> bool:
        if property_name != 'rating':
            return True
        if not (isinstance(new_value, float) or isinstance(new_value, int)):
            print("ERROR: Rating should be float or int")
            return False
        if new_value<0:
            print("ERROR: Film cant be worst than \"The Room\"")
            return False
        if new_value > 10:
            print("ERROR: Film cant be better than 10")
            return False
        if old_value == new_value:
            print("ATTENTION: Title changed to the same value")
            return True
        return True
#endregion

#region Loggers
class ConsoleLog(PropertyChangedListenerProtocol):
    def on_property_changed(self, obj: DataChangedProtocol, property_name: str) -> None:
        print(f"!{str(obj)} was edited in: {property_name}")
#endregion

#region Test
class Film(DataChangedProtocol, DataChangingProtocol):
    title: str
    year: int
    rating: float
    
    __data_changed_listeners: list[DataChangedProtocol]
    __data_changing_listeners: list[DataChangingProtocol]

    def __init__(self, title: str, year: int, rating: float) -> None:
        self.__data_changed_listeners = list()
        self.__data_changing_listeners = list()
        self._title = None
        self._year = None
        self._rating = None
        self.title = title
        self.year = year
        self.rating = rating
#region Properties
    @property
    def title(self) -> str:
        return self._title

    @property
    def year(self) -> int:
        return self._year

    @property
    def rating(self) -> float:
        return self._rating
#endregion
#region Setters
    @title.setter
    def title(self, title: str) -> None:
        if self._on_property_changing('title', self.title, title)!=True:
            return
        self._title = title
        self._successfully_changed('title')

    @year.setter
    def year(self, year: int) -> None:
        if self._on_property_changing('year', self.year, year)!=True:
            return
        self._year = year
        self._successfully_changed('year')

    @rating.setter
    def rating(self, rating: float) -> None:
        if self._on_property_changing('rating', self.rating, rating)!=True:
            return
        self._rating = rating
        self._successfully_changed('rating')
#endregion

    def add_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        if listener not in self.__data_changed_listeners: self.__data_changed_listeners.append(listener)

    def remove_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        if listener in self.__data_changed_listeners: self.__data_changed_listeners.remove(listener)

    def add_property_changing_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        if listener not in self.__data_changing_listeners: self.__data_changing_listeners.append(listener)

    def remove_property_changing_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        if listener in self.__data_changed_listeners: self.__data_changing_listeners.remove(listener)

    def _on_property_changing(self, property_name: str, old_value: Any, new_value: Any) -> bool:
        return all(listener.on_property_changing(self, property_name, old_value, new_value) for listener in self.__data_changing_listeners)

    def _successfully_changed(self, property_name: str) -> None:
        for listener in self.__data_changed_listeners: listener.on_property_changed(self, property_name)

    def __str__(self):
        return f"\"{self._title}\" ({self._year})"
#endregion

#actual code
film = Film("Wolf from Wall Street", 2013, 8.2)

log = ConsoleLog()
title_validator = TitleValidator()
year_validator = YearValidator()
rating_validator = RatingValidator()

film.add_property_changed_listener(log)
film.add_property_changing_listener(title_validator)
film.add_property_changing_listener(year_validator)
film.add_property_changing_listener(rating_validator)

print(f"До изменений: {str(film)} {film.rating}/10")

print()
print("Недопустимые изменения")
film.title = ""
film.title = 123
film.year = 1369
film.year = 2077
film.rating = -5
film.rating = 12
print()
print(f"После недопустимых изменений: {str(film)} {film.rating}/10")
print(f"Изменений ожидаемо нет")

print()
print("Допустимые изменения")
film.title = "Once upon a time... in Hollywood"
film.year = 2019
film.rating = 10
print()
print(f"После корректных изменений: {str(film)} {film.rating}/10")