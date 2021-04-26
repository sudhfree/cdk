from json import JSONEncoder


class NotificationEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__


class NSuiteNotification(JSONEncoder):

    def __init__(self, **kwargs):
        self.module_name = "invoice"
        self.service = "upsertInvoice"
        self.spread = True
        self.args = {"tranid": "", "values": {}}
        self.args["values"]["custbody_ihm_ready_to_print"] = True

    def toJSON(self):
        """
        Returns a JSON dictionary object of this LogEntry
        """
        return self.__dict__
