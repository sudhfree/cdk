import json
import os
import traceback
import boto3
from botocore.exceptions import ClientError
from api.config.AppSettings import AppSettings


class LogQueueService(object):
    """
    The LogQueueService class sends log messages to a configured
    SQS message queue.
    """
    queue_name: str = None
    queue_url: str = None
    log_level: str = None

    EMPTY = ''
    """
    Constructor method uses **kwargs dictionary to initialize
    the service.
    """

    def __init__(self, _app_settings: AppSettings):
        self.queue_url = _app_settings.logging_queue_url
        self.__validate_configuration__

    def __validate_configuration__(self):
        """
        Validate that the Service has been properly initialized.
        """
        if self.queue_url is None or self.queue_url == self.EMPTY:
            raise Exception('LogQueueService was not configured. {}'.format(self.queue_url))
        return

    # send Message object to specified Queue Name
    """
    Sends message to the SQS message queue.
    """

    def send_sqs_message(self, message):
        result = False
        try:
            sqs_client = boto3.client('sqs')
            msg = sqs_client.send_message(QueueUrl=self.queue_url, MessageBody=message)
            result = message
        except ClientError as ce:
            print("Error sending message to SQS {}".format(self.queue_url))
            stack = traceback.format_exc()
            print('Stack: {}'.format(stack))
        return result
