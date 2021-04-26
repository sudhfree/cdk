from api.config import app_constants as constants
from api.models.ApiNotification import ApiNotification
import botocore
from botocore.exceptions import ClientError
import boto3
from api.services.IhmBaseLogger import IhmBaseLogger
from api.config.AppSettings import AppSettings
from api.exceptions.NotificationError import NotificationError


class SnsResponse():
    MessageId = constants.EMPTY
    SequenceNumber = constants.EMPTY

    def __init__(self, _settings: AppSettings):
        self.MessageId = dict['MessageId']
        self.SequenceNumber = dict['SequenceNumber']
        return


class NotificationService():
    settings: AppSettings = None
    sns_endpoint = ""
    logger: IhmBaseLogger = None
    gateway_url: str = None
    region: str = None
    adjustment_queue = None

    def __init__(self, settingsIn: AppSettings = None):
        self.settings = settingsIn
        self.sns_endpoint = settingsIn.sns_endpoint
        self.adjustment_queue = settingsIn.adjustment_queue_url
        self.logger = IhmBaseLogger.get_logger(settingsIn)
        self.gateway_url = settingsIn.gateway_url
        self.region = settingsIn.region

    def send_message(self, event_type, route, id, resourceType, actor="not provided", isAdjustment: bool = False):
        get_url = self.__build_request_url(self.gateway_url, route, id)
        notification = ApiNotification(event_type, id, actor, get_url, resourceType, isAdjustment)
        if notification.isAdjustment is None:
            notification.isAdjustment = False
        self.__send_sns_notification(notification)
        return

    def __send_sns_notification(self, notification):
        try:
            print("Sending Notification for {} Method for id {}. notification= {}".format(notification.eventType, notification.id, notification.__dict__))
            self.logger.info("Sending Notification {} for id {} to SNS: {}".format(notification.__dict__, notification.id, self.sns_endpoint))
            sns = boto3.client('sns', region_name=self.region)
            #attr_value = False if notification.isAdjustment is None else notification.isAdjustment
            msg_attributes = { "isAdjustment" : { "DataType": "String", "StringValue": str(notification.isAdjustment)}}
            print("MessageAttributes={}".format(str(msg_attributes)))
            print("Publishing notification to ={}".format(str(self.sns_endpoint)))
            self.logger.info("Publishing notification to ={}".format(str(self.sns_endpoint)))
            response = sns.publish(TopicArn=self.sns_endpoint, Message=str(notification.toJSON()), MessageStructure="str", MessageAttributes = msg_attributes)
            #print("SNS Response={}".format(str(response)))
            # if notification.isAdjustment:
            #     response = sns.publish(TopicArn=self.adjustment_queue, Message=str(notification.toJSON()), MessageStructure="str")
            # else:
            #     response = sns.publish(TopicArn=self.sns_endpoint, Message=str(notification.toJSON()), MessageStructure='str')
            self.logger.info("SNS Message sent. Response: {}".format(response))
        except botocore.exceptions.ClientError as e:
            self.logger.error("Error occurred sending SNS message. {}".format(e))
            raise NotificationError("Failed to send Notification {} for id {} to SNS: {}: Error: {}".format(notification.__dict__, notification.id, self.sns_endpoint, str(e)))

    def __build_request_url(self, base_url, route, id):
        return base_url + route + "/" + str(id)
