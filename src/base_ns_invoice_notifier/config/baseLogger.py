import json
import time
import traceback

from logQueueService import LogQueueService


class IhmBaseLogger:
    """
    IhmBaseLogger provides methods for logging structured log
    data messages.
    """

    INFO = 'INFO'
    DEBUG = 'DEBUG'
    WARNING = 'WARNING'
    WARN = 'WARN'
    ERROR = 'ERROR'
    FATAL = 'FATAL'

    APPLICATION_NAME = "app_name"
    QUEUE_NAME = "queue_name"
    LOG_LEVEL = "log_level"
    COMPONENT_NAME = 'component'
    PROCESS_ID = 'process_id'
    RECORD_ID = 'record_id'
    RECORD_TYPE = 'record_type'
    TRACKGING_REQ_ID = "tracking_request_id"
    STACKTRACE = 'stacktrace'
    MESSAGE = 'msg'
    EMPTY = ""

    app_name = EMPTY
    component_name = EMPTY
    log_level = INFO
    queueService = None

    current_time = lambda self: int(round(time.time() * 1000))
    log_to_cw = False

    # TODO: For local dev define variable to allow output to Cloudwatch....

    def __init__(self, **kwargs):
        """
       Constructor method that takes in configuration settings from
       input **kwargs dictionary.

       Passing **kwargs parameters:
       Configuration parameters can be passed as a dictionary of key value pairs

       """
        self.__configure(**kwargs)
        self.queueService = LogQueueService(**kwargs)

    def __init__(self, app_name, queue_url, log_level, **kwargs):
        """
        Constructor method that takes in configuration settings using
        *args

        Passing *args parameters:
        app_name = name of top level application
        queue_url = name of SQS message queue
        log_level = default log level
        """
        kwargs.update(app_name=app_name, queue_url=queue_url, log_level=log_level)
        self.__configure(**kwargs)
        self.queueService = LogQueueService(**kwargs)

    def __configure(self, **kwargs):
        for key, value in kwargs.items():
            if key == self.LOG_LEVEL:
                self.log_level = value
            elif key == self.APPLICATION_NAME:
                self.app_name = value
            elif key == self.COMPONENT_NAME:
                self.component_name = value
        self.__validate_configuration()

    def __validate_configuration(self):
        """
        Validate that the Service has been properly initialized.
        """
        if self.app_name is None or self.app_name is self.EMPTY:
            raise Exception('IhmBaseLogger was not configured. {} = {}'.format(self.APPLICATION_NAME, self.app_name))
        return

    def fatal(self, msg, *args, **kwargs):
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
        msg = self.__format_message(msg, *args)
        stack = traceback.format_exc()
        kwargs.update({'stacktrace': stack})
        self.__log_message(self.FATAL, msg, **kwargs)

    def error(self, msg, *args, **kwargs):
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
        msg = self.__format_message(msg, *args)
        stack = traceback.format_exc()
        kwargs.update({'stacktrace': stack})
        self.__log_message(self.ERROR, msg, **kwargs)

    def warn(self, msg, *args, **kwargs):
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
        msg = self.__format_message(msg, *args)
        self.__log_message(self.WARNING, msg, **kwargs)

    def warning(self, msg, *args, **kwargs):
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
        msg = self.__format_message(msg, *args)
        self.__log_message(self.WARNING, msg, **kwargs)

    def info(self, msg, *args, **kwargs):
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
        msg = self.__format_message(msg, *args)
        self.__log_message(self.INFO, msg, **kwargs)

    def debug(self, msg, *args, **kwargs):
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
        msg = self.__format_message(msg, *args)
        self.__log_message(self.DEBUG, msg, **kwargs)

    def isWarnLevel(self):
        """
        Checks if current log level is WARN or WARNING.
        Returns True or False
        """
        if self.log_level == self.WARNING or self.log_level == self.WARN\
                or self.log_level == self.INFO or self.log_level == self.DEBUG:
            return True
        return False

    def isInfoLevel(self):
        """
        Checks if current log level is INFO.
        Returns True or False
        """
        if self.log_level == self.INFO or self.log_level == self.DEBUG:
            return True
        return False

    def isDebugLevel(self):
        """
        Checks if current log level is DEBUG.
        Returns True or False
        """
        if self.log_level == self.DEBUG:
            return True
        return False

    def get_log_level(self):
        """
        Returns current log level.
        """
        return self.log_level

    def __log_message(self, level, msg, **kwargs):
        """
        Construct a formatted LogEntry and the log it.
        """
        log_entry = self.LogEntry()
        log_entry.timestamp = self.current_time()
        log_entry.log_level = level
        log_entry.application = self.app_name
        log_entry.component = self.get_component_name(**kwargs)
        log_entry.record_id = self.get_record_id(**kwargs)
        log_entry.record_type = self.get_record_type(**kwargs)
        log_entry.tracking_request_id = self.get_tracking_request_id(**kwargs)
        log_entry.msg = msg
        log_entry.stacktrace = self.get_stacktrace(**kwargs)
        self.__log(log_entry)
        return

    def __format_message(self, msg, *args):
        """
        Formats the input message with *args parameters and then
        returns the message
        """
        if args is not None and len(args) != 0:
            msg = msg.format(*args)
        return msg

    def __log(self, message):
        """
        Uses LogQueueService and sends log message
        """
        self.queueService.send_sqs_message(message.toJSON())
        if self.log_to_cw is True:
            print(message.toJSON())
        return

    def get_stacktrace(self, **kwargs):
        """
        Returns a String of the current stack trace from the **kwargs
        dictionary or an empty string.
        """
        for key, value in kwargs.items():
            if key == 'stacktrace':
                return value
        return self.EMPTY

    def get_component_name(self, **kwargs):
        """
        Returns a string with the component name from **kwargs dictionary
        or an empty string.
        """
        try:
            if self.component_name == self.EMPTY:
                for key, value in kwargs.items():
                    if key == self.COMPONENT_NAME:
                        self.component_name = value

            if self.component_name is self.EMPTY:
                raise Exception('IhmBaseLogger.get_component_name() - component_name not set!')
        except Exception as e:
            print("IhmBaseLogger Exception {}".format(e))
            raise e
        return self.component_name

    def get_process_id(self, **kwargs):
        """
        Returns the process_id from the **kwargs dictionary or an empty string.
        """
        for key, value in kwargs.items():
            if key == self.PROCESS_ID:
                return value
        return ''

    def get_record_id(self, **kwargs):
        """
        Returns the record_id from the **kwargs dictionary or an empty string.
        """
        for key, value in kwargs.items():
            if key == self.RECORD_ID:
                return value
        return ''

    def get_record_type(self, **kwargs):
        """
        Returns the record_type from the **kwargs dictionary or an empty string.
        """
        for key, value in kwargs.items():
            if key == self.RECORD_TYPE:
                return value
        return ''

    def get_tracking_request_id(self, **kwargs):
        """
        Returns the record_type from the **kwargs dictionary or an empty string.
        """
        for key, value in kwargs.items():
            if key == self.TRACKGING_REQ_ID:
                return value
        return ''

    def enable_log_to_cloudwatch(self, value):
        if isinstance(bool, value):
            self.log_to_cw = value
        return self.log_to_cw

    class LogEntry(object):
        """
        LogEntry is an internal class used to define the
        structured log message format.
        """

        def toJSON(self):
            """
            Returns a JSON string for this object.
            """
            return json.dumps(self.__dict__)
