from __future__ import annotations
from typing import Protocol, Optional, Any, Dict
import json

text = ""
volume = 0
media_player = False

output_file = "output.txt"
binds_file = "binds.json"
default_binds_file = "default_binds.json"

#region Protocols
class Command(Protocol):
    def exec(self) -> None:
        ...

    def undo(self) -> None:
        ...

    def redo(self) -> None:
        ...
#endregion

#region Commands
class KeyCommand(Command):
    def __init__(self, char: str) -> None:
        self.char = char

    def exec(self) -> str:
        global text
        text += self.char
        return text

    def undo(self) -> str:
        global text
        text = text[:-1]
        return text

    def redo(self) -> str:
        return self.exec()

class VolumeUpCommand(Command):
    def __init__(self, amount: int = 20) -> None:
        self.amount = amount

    def exec(self) -> str:
        global volume
        volume += self.amount
        return f"volume increased +{self.amount}% ({volume}%)"

    def undo(self) -> str:
        global volume
        volume -= self.amount
        return f"volume decreased +{self.amount}% ({volume}%)"

    def redo(self) -> str:
        return self.exec()

class VolumeDownCommand(Command):
    def __init__(self, amount: int = 20) -> None:
        self.amount = amount

    def exec(self) -> str:
        global volume
        volume -= self.amount
        return f"volume decreased -{self.amount}% ({volume}%)"

    def undo(self) -> str:
        global volume
        volume += self.amount
        return f"volume increased -{self.amount}% ({volume}%)"

    def redo(self) -> str:
        return self.exec()

class MediaPlayerCommand(Command):
    def __init__(self) -> None:
        pass
    def exec(self) -> str:
        global media_player
        media_player = True
        return "media player launched"

    def undo(self) -> str:
        global media_player
        media_player = False
        return "media player closed"

    def redo(self) -> str:
        return self.exec()
#endregion

class Memento:
    def __init__(self, state: Dict[str, Any]) -> None:
        self.state = state

    @classmethod
    def file_load(cls, filename: str):
        try:
            with open(filename, "r") as f:
                state = json.load(f)
            return cls(state)
        except Exception as e:
            print(f"ERROR: {e}")
            return None

    def file_save(self, filename: str) -> bool:
        try:
            with open(filename, "w") as f:
                json.dump(self.state, f, indent=4)
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False

class Keyboard:
    def __init__(self) -> None:
        self.key_binds: dict[str, Command] = {}
        self.back_history: list[dict[str, Command]] = []
        self.forward_history: list[dict[str, Command]] = []

        if (self._state_load(binds_file) == 1): pass
        else: self.back_to_default_binds()

    def back_to_default_binds(self) -> None:
        self.logger(essential="Back to default binds")
        self._state_load(filename=default_binds_file)
        self._state_save()

    def key_bind(self, key: str, command: Optional[Command]) -> None:
        self.key_binds[key] = command

    def logger(self, command: str="", message: str="", essential: str=""):
        with open(output_file, "a") as file:
            if message!="":file.write(message + "\n")
        if command!="":command+=": "
        if message!="":message+=" "
        print(f"{command}{message}{essential}")

    def press(self, key: str) -> str | None:
        if key == "undo":
            return self.undo()
        elif key == "redo":
            return self.redo()

        command = self.key_binds.get(key)
        if not command and len(key) == 1:
            self.key_bind(key, KeyCommand(key))
            command = self.key_binds.get(key)
        if command:
            result = command.exec()
            self.back_history.append({"key": key, "command": command})
            self.forward_history.clear()
            self.logger(message=result)
            return result
        print(f"ERROR: Unknown key: {key}")
        return f"Unknown key: {key}"

    def undo(self) -> None:
        if not self.back_history:
            self.logger(essential = "History empty")

        command = self.back_history.pop()
        result = command["command"].undo()
        self.forward_history.append(command)
        self.logger(command = "undo", message = result)

    def redo(self) -> str:
        if not self.forward_history:
            self.logger(essential = "History empty")

        command = self.forward_history.pop()
        result = command["command"].redo()
        self.back_history.append(command)
        self.logger(command = "redo", message = result)

    def get_state(self) -> Dict[str, Any]:
        global text, volume, media_player

        key_binds = {}
        for key, command in self.key_binds.items():
            if command is None:
                key_binds[key] = None
            else:
                key_binds[key] = {
                    'class': command.__class__.__name__,
                    'state': command.__dict__.copy()
                }

        return {
            'text': text,
            'volume': volume,
            'media_player': media_player,
            'key_binds': key_binds,
            'back_history': [cmd["key"] for cmd in self.back_history],
            'forward_history': [cmd["key"] for cmd in self.forward_history]
        }

    def set_state(self, state: Dict[str, Any]) -> bool:
        global text, volume, media_player

        try:
            text = state['text']
            volume = state['volume']
            media_player = state['media_player']

            class_names = {cls.__name__: cls for cls in Command.__subclasses__()}

            self.key_binds.clear()
            for key, cmd_data in state.get('key_binds', {}).items():
                if cmd_data is None:
                    self.key_binds[key] = None
                else:
                    cls = class_names[cmd_data['class']]
                    self.key_binds[key] = cls(**cmd_data['state'])

            self.back_history = [
                {"key": key, "command": self.key_binds[key]}
                for key in state.get('back_history', [])
                if key in self.key_binds and self.key_binds[key] is not None
            ]

            self.forward_history = [
                {"key": key, "command": self.key_binds[key]}
                for key in state.get('forward_history', [])
                if key in self.key_binds and self.key_binds[key] is not None
            ]
            return True
        except Exception as e:
            print(f"Error setting state: {e}")
            return False

    def _state_save(self, filename: str = binds_file) -> None:
        memento = Memento(self.get_state())
        if memento.file_save(filename):
            self.logger(essential="State saved")

    def _state_load(self, filename: str = binds_file) -> bool:
        memento = Memento.file_load(filename)
        if memento and self.set_state(memento.state):
            self.logger(essential="State loaded")
            return True
        return False

#actual code
keyboard = Keyboard()

keyboard.press("a")
keyboard.press("b")
keyboard.press("c")
keyboard.press("undo")
keyboard.press("undo")
keyboard.press("redo")
keyboard.press("ctrl++")
keyboard.press("ctrl+-")
keyboard.press("ctrl+p")
keyboard.press("d")
keyboard.press("undo")
keyboard.press("undo")

keyboard._state_save()