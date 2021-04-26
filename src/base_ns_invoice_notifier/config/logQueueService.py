import json
import os
import traceback
import boto3
from botocore.exceptions import ClientError


class LogQueueService:
    """
    The LogQueueService class sends log messages to a configured
    SQS message queue.
    """
    queue_name = ''
    queue_url = ''
    log_level = ''

    EMPTY = ''
    # Set to default MessageQueue name.....
    MSG_QUEUE_NAME = 'queue_name'
    LOG_LEVEL = 'log_level'
    QUEUE_URL = "queue_url"
    REGION = "region"

    def __init__(self, **kwargs):
        """
        Constructor method uses **kwargs dictionary to initialize
        the service.
        """
        self.configure(**kwargs)

    def __configure__(self, **kwargs):
        """
        Inner class method used to configure Service settings
        like queue name, application name, log level, and optional
        component name.
        """
        for key, value in kwargs.items():
            if key is self.MSG_QUEUE_NAME:
                self.queue_name = value
            elif key is self.QUEUE_URL:
                self.queue_url = value
            elif key is self.LOG_LEVEL:
                self.log_level = value
            elif key is self.REGION:
                self.region = value
        return

    def configure(self, **kwargs):
        """
        Configuration method that initializes Service settings
        then validates for errors.
        """
        try:
            self.__configure__(**kwargs)
            if self.queue_name == self.EMPTY:
                self.queue_name = os.getenv(self.MSG_QUEUE_NAME)
            if self.queue_url == self.EMPTY:
                self.queue_url = os.getenv(self.QUEUE_URL)
            if self.log_level == self.EMPTY:
                self.log_level = os.getenv(self.LOG_LEVEL)
            self.__validate_configuration__()
        except Exception as e:
            print("LogQueueService configuration Exception {}".format(e))
            stack = traceback.format_exc()
            print('Stack: {}'.format(stack))
            raise e
        return

    def __validate_configuration__(self):
        """
        Validate that the Service has been properly initialized.
        """
        if self.queue_url is None or self.queue_url == self.EMPTY:
            raise  Exception('LogQueueService was not configured. {} = {}'.format(self.QUEUE_URL, self.queue_url))
        # if self.queue_name is None or self.queue_name == self.EMPTY:
        #     raise Exception('LogQueueService was not configured. {} = {}'.format(self.MSG_QUEUE_NAME, self.queue_name))
        return

    # get an SQS URL by queue name
    def get_queue_url(self, queue_name):
        """
        Returns the URL for the input queue_name.
        """
        queue_url = ""
        try:
            sqs_client = boto3.client('sqs', region_name="us-east-1")
            queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
        except Exception as e:
            print("AWS Boto3 exception!")
            stack = traceback.format_exc()
            print('Stack: {}'.format(stack))
            raise e
        return queue_url

    # send Message object to specified Queue Name
    def send_sqs_message(self, message):
        """
        Sends message to the SQS message queue.
        """
        result = False
        queue_url = ""
        try:
            sqs_client = boto3.client('sqs')
            # queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
            if self.queue_url == self.EMPTY:
                queue_url = self.get_queue_url(self.queue_name)
            else:
                queue_url = self.queue_url
            msg = sqs_client.send_message(QueueUrl=queue_url,
                                          MessageBody=message)

            #TODO: May have to handle retries if SQS queue gets overloaded.
            result = message
        except ClientError as ce:
            print("Error sending message to SQS {}".format(self.queue_name))
            stack = traceback.format_exc()
            print('Stack: {}'.format(stack))
        return result

    def set_log_level(self, level):
        """
        Sets log_level
        """
        self.log_level = level

    def get_log_level(self):
        """
        Returns current log level.
        """
        return self.log_level

    def set_queue_name(self, value):
        """
        Sets the name for the SQS message queue used by the service
        """
        if value is not None and value != "":
            self.queue_name = value

    def get_queue_name(self):
        """
        Returns the name of the SQS message queue
        """
        return self.queue_name
