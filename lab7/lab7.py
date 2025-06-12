from typing import Type, Generator, Any, Callable, Optional, TypeVar, Protocol
from contextlib import contextmanager

T = TypeVar('T')

class LifeStyle:
    PER_REQUEST = "PerRequest"
    SCOPED = "Scoped"
    SINGLETON = "Singleton"

#region Example Protocols
class MultiplyProtocol(Protocol):
    def exec(self, num: float) -> None:
        ...

class SubstractProtocol(Protocol):
    def exec(self, num: float) -> None:
        ...

class DifferenceProtocol(Protocol):
    def exec(self, num: float) -> None:
        ...
#endregion

#region Example Classes
class MultiplyByFive(MultiplyProtocol):
    def exec(self, num: float) -> None:
        return num*5

class Square(MultiplyProtocol):
    def exec(self, num: float) -> None:
        return num * num

class SubstractByTwo(SubstractProtocol):
    def exec(self, num: float) -> None:
        return num/2

class IsEven(SubstractProtocol):
    def exec(self, num: float) -> None:
        return num%2==0

class DifferenceFromFive(DifferenceProtocol):
    def exec(self, num: float) -> None:
        return 5-num

class DifferenceFromSquare(DifferenceProtocol):
    def exec(self, num: float) -> None:
        return (num-1)*num
#endregion

class Injector:
    def __init__(self) -> None:
        self._registrations: dict[Type, dict] = {}
        self._singleton_instances: dict[Type, Any] = {}
        self._scoped_instances: dict[Type, Any] = {}
        self._in_scope = False

    def register(self,
                 protocol_type: Type[T],
                 class_type: Optional[Type] = None,
                 life_style: str = LifeStyle.PER_REQUEST,
                 factory_method: Optional[Callable] = None,
                 params: Optional[dict] = None) -> None:

        if factory_method and class_type:
            raise ValueError()

        self._registrations[protocol_type] = {
            'class_type': class_type,
            'life_style': life_style,
            'params': params or {},
            'factory_method': factory_method
        }

    @contextmanager
    def scope(self) -> Generator[None, Any, None]:
        if self._in_scope:
            yield
            return

        self._in_scope = True
        self._scoped_instances.clear()
        try:
            yield
        finally:
            self._in_scope = False
            self._scoped_instances.clear()

    def get_instance(self, protocol_type: Type[T]) -> T:
        if protocol_type not in self._registrations:
            raise ValueError(f"No registration found for {protocol_type.__name__}")

        registration = self._registrations[protocol_type]
        life_style = registration['life_style']

        if life_style == LifeStyle.SINGLETON:
            if protocol_type in self._singleton_instances:
                return self._singleton_instances[protocol_type]

            instance = self.create_instance(registration)
            self._singleton_instances[protocol_type] = instance
            return instance

        if life_style == LifeStyle.SCOPED:
            if protocol_type in self._scoped_instances:
                return self._scoped_instances[protocol_type]

            instance = self.create_instance(registration)
            self._scoped_instances[protocol_type] = instance
            return instance

        return self.create_instance(registration)

    def create_instance(self, registration: dict) -> Any:
        if registration['factory_method']:
            return registration['factory_method']()

        class_type = registration['class_type']
        params = registration['params'].copy()
        constructor_params = {}
        if hasattr(class_type, '__annotations__'):
            for param_name, param_type in class_type.__annotations__.items():
                if param_name != 'return' and param_type in self._registrations:
                    constructor_params[param_name] = self.get_instance(param_type)

        constructor_params.update(params)

        return class_type(**constructor_params)

#actual code
injector = Injector()
injector.register(MultiplyProtocol, MultiplyByFive, LifeStyle.SINGLETON)
injector.register(SubstractProtocol, SubstractByTwo, LifeStyle.SCOPED)
injector.register(DifferenceProtocol, DifferenceFromFive, LifeStyle.PER_REQUEST)

mult1 = injector.get_instance(MultiplyProtocol)
print(mult1.exec(3))
mult2 = injector.get_instance(MultiplyProtocol)
print(f"Сравнение Singleton: {mult1 == mult2}")

with injector.scope():
    mult3 = injector.get_instance(MultiplyProtocol)
    print(f"Сравнение Singleton: {mult1 == mult3}")

    sub1 = injector.get_instance(SubstractProtocol)
    print(sub1.exec(6))
    sub2 = injector.get_instance(SubstractProtocol)
    print(f"Сравнение Scoped: {sub1 == sub2}")

sub3 = injector.get_instance(SubstractProtocol)
print(f"Сравнение Scoped: {sub1 == sub3}")

if injector._registrations[DifferenceProtocol]['life_style'] == LifeStyle.PER_REQUEST:
    with injector.scope():
        diff1 = injector.get_instance(DifferenceProtocol)
        print(diff1.exec(7))
        diff2 = injector.get_instance(DifferenceProtocol)
        print(f"Сравнение PerRequest: {diff1 == diff2}")