import datetime
from api.config import app_constants as constants


class ApiNotification:
    resource = "Orders"
    eventType = constants.EMPTY
    timestamp = constants.EMPTY
    id = constants.EMPTY
    GETLink = constants.EMPTY
    actor = constants.EMPTY
    isAdjustment: bool = False

    def __init__(self, event_type, id, actor, url, resourceType, isAdjustment: bool):
        self.resource = resourceType
        self.eventType = event_type
        self.id = id
        self.actor = actor
        self.GETLink = url
        self.isAdjustment = isAdjustment
        self.timestamp = str(datetime.datetime.now())
        return

    def toJSON(self):
        """
        Returns a JSON dictionary object of this LogEntry
        :return:
        """
        return self.__dict__
