import json
import time
import traceback
from pydantic import BaseModel, Field
from typing import Set, List, Optional, TypeVar
from services.LogQueueService import LogQueueService
import config.AppSettings as _settings
import sys
"""
IhmBaseLogger provides methods for logging structured log
data messages.
"""
class IhmBaseLogger(object):
    _logger = None #static instance of self/logger to support singleton
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    WARNING = 'WARNING'
    WARN = 'WARN'
    ERROR = 'ERROR'
    FATAL = 'FATAL'

    DEFAULT_APPLICATION_NAME: str
    DEFAULT_LOG_LEVEL: str
    DEFAULT_COMPONENT_NAME: str
    DEFAULT_PROCESS_ID: Optional[str]="Not provided"
    DEFAULT_RECORD_ID: str
    DEFAULT_RECORD_TYPE: str
    DEFAULT_TRACKING_REQ_ID: Optional[str]="Not provided"
    DEFAULT_STACKTRACE: Optional[str]="Not provided"
    DEFAULT_MESSAGE: Optional[str]="Not provided"
    EMPTY = ""

    KEY_APPLICATION_NAME = "application_name"
    KEY_LOG_LEVEL="log_level"
    KEY_COMPONENT_NAME="component_name"
    KEY_PROCESS_ID="process_id"
    KEY_RECORD_ID="record_id"
    KEY_RECORD_TYPE="record_type"
    KEY_TRACKING_REQ_ID="tracking_request_id"
    KEY_STACKTRACE="stacktrace"
    KEY_MESSAGE="message"

    queueService: LogQueueService = None
    current_time: int = lambda self: int(round(time.time() * 1000))
    log_to_cw: bool = False

    @staticmethod
    def get_logger(settingsIn: _settings.AppSettings=None):
        """ Static access method. """
        if IhmBaseLogger._logger == None:
                #initialize if never done before
                IhmBaseLogger(settingsIn)
        return IhmBaseLogger._logger

    """
        called only once when instance is created.  uses values in settings to initialize all defaults. 
        Also sets the current values for first time use.
        
           TODO:
           - Optional vs required fields

        """
    def __init__(self, appSettings: _settings.AppSettings=None, **kwargs):
        if IhmBaseLogger._logger != None:
            raise Exception("This class is a singleton!")
        else:
            IhmBaseLogger._logger = self
            if appSettings==None :
                raise Exception("settings must be passed to get_logger the first time its executed")
            else:
                settingsValues = appSettings.dict()
                self.queueService = LogQueueService(appSettings)
                self.DEFAULT_LOG_LEVEL = appSettings.log_level
                self.DEFAULT_APPLICATION_NAME = appSettings.application_name
                self.DEFAULT_COMPONENT_NAME = appSettings.component_name
                self.DEFAULT_RECORD_ID=self.EMPTY
                self.DEFAULT_RECORD_TYPE=self.EMPTY
                self.DEFAULT_TRACKING_REQ_ID=self.EMPTY
                # set all the defaults to do

    """
    Log a FATAL level message. The user does not have to pass in an exception
    object as the method will automatically capture the last exception
    captured by the Python interpreter and add it to **kwargs.

    Parameters:
    msg = the log message with optional comma separated values in *args
    **kwargs = dictionary of additional values for:
       - component_name
       - record_id  (Optional)
       - record_type (Optional)
       TODO:
       - tracking_request_id (Optional)

    """
    def fatal(self, msg, *args, **kwargs):
        msg = self.__format_message(msg, *args)
        stack = traceback.format_exc()
        kwargs.update({'stacktrace': stack})
        self.__log_message(self.FATAL, msg, **kwargs)

    """
      Log a ERROR level message. The user does not have to pass in an exception
      object as the method will automatically capture the last exception
      captured by the Python interpreter and add it to **kwargs.

      Parameters:
      msg = the log message with optional comma separated values in *args
      **kwargs = dictionary of additional values for:
          - component_name
          - record_id  (Optional)
          - record_type (Optional)
          - process_id  (Optional)
          - tracking_request_id (Optional)

    """
    def error(self, msg, *args, **kwargs):

        msg = self.__format_message(msg, *args)
        stack = traceback.format_exc()
        kwargs.update({'stacktrace': stack})
        self.__log_message(self.ERROR, msg, **kwargs)

    """
      Log a WARN level message.

      Parameters:
      msg = the log message with optional comma separated values in *args
      **kwargs = dictionary of additional values for:
          - component_name
          - record_id  (Optional)
          - record_type (Optional)
          - process_id  (Optional)

    """
    def warn(self, msg, *args, **kwargs):

        msg = self.__format_message(msg, *args)
        self.__log_message(self.WARNING, msg, **kwargs)

    """
      Log a WARNING level message.

      Parameters:
      msg = the log message with optional comma separated values in *args
      **kwargs = dictionary of additional values for:
          - component_name
          - record_id  (Optional)
          - record_type (Optional)
          - process_id  (Optional)

    """
    def warning(self, msg, *args, **kwargs):

        msg = self.__format_message(msg, *args)
        self.__log_message(self.WARNING, msg, **kwargs)

    """
      Log an INFO level message.

      Parameters:
      msg = the log message with optional comma separated values in *args
      **kwargs = dictionary of additional values for:
          - component_name
          - record_id  (Optional)
          - record_type (Optional)
          - process_id  (Optional)

            """
    def info(self, msg, *args, **kwargs):

        msg = self.__format_message(msg, *args)
        self.__log_message(self.INFO, msg, **kwargs)

    """
      Log a DEBUG message.

      Parameters:
      msg = the log message with optional comma separated values in *args
      **kwargs = dictionary of additional values for:
          - component_name
          - record_id  (Optional)
          - record_type (Optional)
          - process_id  (Optional)
    """
    def debug(self, msg, *args, **kwargs):
        msg = self.__format_message(msg, *args)
        self.__log_message(self.DEBUG, msg, **kwargs)

    def __log_message(self, level, msg, **kwargs):
        """
        Construct a formatted LogEntry and the log it.
        """
        #create a new log entry
        log_entry = IhmBaseLogger.LogEntry(self, level, msg, **kwargs)
        self.queueService.send_sqs_message(log_entry.toJSON())
        if self.log_to_cw is True:
            print(log_entry.toJSON())
        return

    def __format_message(self, msg, *args):
        """
        Formats the input message with *args parameters and then
        returns the message
        """
        if args is not None and len(args) != 0:
            msg = msg.format(*args)
        return msg

    def enable_log_to_cloudwatch(self, value):
        if isinstance(bool, value):
            self.log_to_cw = value
        return self.log_to_cw

    class LogEntry(object):
        """
        LogEntry is an internal class used to define the
        structured log message format.
        """
        EMPTY = ""

        def __init__(self, logger_instance, level, msg, **logging_overrides):
            self.timestamp = logger_instance.current_time()
            self.log_level = logger_instance.DEFAULT_LOG_LEVEL
            self.application = logger_instance.DEFAULT_APPLICATION_NAME
            self.component = logger_instance.DEFAULT_COMPONENT_NAME
            self.record_id = logger_instance.DEFAULT_RECORD_ID
            self.record_type = logger_instance.DEFAULT_RECORD_TYPE
            self.tracking_request_id = logger_instance.DEFAULT_TRACKING_REQ_ID
            #override if data provided
            self.msg = msg
            self.log_level=level
            try:
                self.stacktrace = self.getValueFromKWARGS(logger_instance.KEY_STACKTRACE, **logging_overrides)
            except:  # catch *all* exceptions
                e = sys.exc_info()[0]
                print("Oops!  That was no valid number.  Try again...")

        def getValueFromKWARGS(self, name, **kwargs):
            for key, value in kwargs.items():
                if key == name:
                    return value
            return self.EMPTY

        def toJSON(self):
            """
            Returns a JSON string for this object.
            """
            return json.dumps(self.__dict__)


#     """
#         Returns a String of the current stack trace from the **kwargs
#         dictionary or an empty string.
#     """
#    def get_stacktrace(self, **kwargs):
#
#         for key, value in kwargs.items():
#             if key == 'stacktrace':
#                 return value
#         return self.EMPTY
#
#     def get_component_name(self, **kwargs):
#         """
#         Returns a string with the component name from **kwargs dictionary
#         or an empty string.
#         """
#         try:
#             if self.component_name == self.EMPTY:
#                 for key, value in kwargs.items():
#                     if key == self.COMPONENT_NAME:
#                         self.component_name = value
#
#             if self.component_name is self.EMPTY:
#                 raise Exception('IhmBaseLogger.get_component_name() - component_name not set!')
#         except Exception as e:
#             print("IhmBaseLogger Exception {}".format(e))
#             raise e
#         return self.component_name
#
#     def get_process_id(self, **kwargs):
#         """
#         Returns the process_id from the **kwargs dictionary or an empty string.
#         """
#         for key, value in kwargs.items():
#             if key == self.PROCESS_ID:
#                 return value
#         return ''
#
#     def get_record_id(self, **kwargs):
#         """
#         Returns the record_id from the **kwargs dictionary or an empty string.
#         """
#         for key, value in kwargs.items():
#             if key == self.RECORD_ID:
#                 return value
#         return ''
#
#     def get_record_type(self, **kwargs):
#         """
#         Returns the record_type from the **kwargs dictionary or an empty string.
#         """
#         for key, value in kwargs.items():
#             if key == self.RECORD_TYPE:
#                 return value
#         return ''
#
#     def get_tracking_request_id(self, **kwargs):
#         """
#         Returns the record_type from the **kwargs dictionary or an empty string.
#         """
#         for key, value in kwargs.items():
#             if key == self.TRACKGING_REQ_ID:
#                 return value
#         return ''
# """
#
# # """
#     Checks if current log level is WARN or WARNING.
#     Returns True or False
# """
# def isWarnLevel(self):
#
#     if self.log_level == self.WARNING or self.log_level == self.WARN\
#             or self.log_level == self.INFO or self.log_level == self.DEBUG:
#         return True
#     return False
#
# def isInfoLevel(self):
#     """
#     Checks if current log level is INFO.
#     Returns True or False
#     """
#     if self.log_level == self.INFO or self.log_level == self.DEBUG:
#         return True
#     return False
#
# def isDebugLevel(self):
#     """
#     Checks if current log level is DEBUG.
#     Returns True or False
#     """
#     if self.log_level == self.DEBUG:
#         return True
#     return False

# def get_log_level(self):
#     """
#     Returns current log level.
#     """
#     return self.log_level