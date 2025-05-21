from typing import Protocol, List
import re, socket

#region Protocols
class LogFilterProtocol(Protocol):
    def match(self, text: str) -> bool:...

class LogHandlerProtocol(Protocol):
    def handle(self, text: str) -> None:...
#endregion

#region Filters
class SimpleLogFilter:
    def __init__(self, pattern: str):
        self.pattern = pattern

    def match(self, text: str) -> bool:
        return self.pattern in text


class ReLogFilter:
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)

    def match(self, text: str) -> bool:
        return bool(self.pattern.search(text))
#endregion

#region Handlers
class ConsoleHandler:
    def handle(self, text: str) -> None:
        print(text)

class FileHandler:
    def __init__(self, filename: str):
        self.filename = filename

    def handle(self, text: str) -> None:
        with open(self.filename, 'a') as f:
            f.write(text + '\n')

class SocketHandler:

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    '''
    def handle(self, text: str) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(text + '\n')
        except:
            raise Exception("Error while sending data")
    '''
    def handle(self, text: str) -> None:
        print(f"\033[94m[SOCKETLOG] {text}\033[0m") #example

class SyslogHandler:
    def handle(self, text: str) -> None:
        print(f"\033[93m[SYSLOG] {text}\033[0m") #example
#endregion

class Logger:
    def __init__(self,filters: List[LogFilterProtocol] = None, handlers: List[LogHandlerProtocol] = None):
        self.filters = []
        self.handlers = []
        if filters!=None: self.filters = filters
        if handlers!=None: self.handlers = handlers

    def log(self, text: str) -> None:
        for filter in self.filters:
            if not filter.match(text):
                return

        for handler in self.handlers:
            handler.handle(text)

#atual test
errorFilter = SimpleLogFilter("ERROR")
warningFilter = SimpleLogFilter("WARNING")
httpFilter = ReLogFilter(r"HTTP/\d\.\d")

consoleHandler = ConsoleHandler()
fileHandler = FileHandler("Log.log")
socketHandler = SocketHandler("testserver", 6969)
syslogHandler = SyslogHandler()

errorLogger = Logger(filters=[errorFilter],handlers=[consoleHandler, fileHandler, syslogHandler])
warningLogger = Logger(filters=[warningFilter],handlers=[consoleHandler, fileHandler])
httpLogger = Logger(filters=[httpFilter],handlers=[consoleHandler, fileHandler, socketHandler])
defaultLogger = Logger(handlers=[consoleHandler])

testLogs = ["INFO: Today is a good day",
            "ERROR: Application is not responding",
            "WARNING: Memory leakage",
            "INFO: HTTP/1.1 request received",
            "ERROR: HTTP/2.0 connection error"]

print("ERROR logs:")
for logText in testLogs:
    errorLogger.log(logText)
print("---------------\nWARNING logs:")
for logText in testLogs:
    warningLogger.log(logText)
print("---------------\nHTTP logs:")
for logText in testLogs:
    httpLogger.log(logText)
print("---------------\nALL logs:")
for logText in testLogs:
    defaultLogger.log(logText)
