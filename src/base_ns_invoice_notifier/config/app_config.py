import os

from baseLogger import IhmBaseLogger
import app_constants as constants
from services.secret_service import SecretsManagerService, SecretsManagerConfigurationException


class AppConfig():

    logger = None
    application_name = constants.EMPTY
    secrets_name = "dev/ns-invoice-notifier/secrets"
    region = "us-east-1"
    env = 'local'
    # mongo_host = 'qa-base-fulfillment-docdb-2.cluster-cgnzhhwlkuak.us-east-1.docdb.amazonaws.com'
    # mongo_port = 27017
    # mongo_user = "dbAdmin"
    # mongo_passwd = "docdbAdmin123"
    # mongo_database = "ihmbase"
    # mongo_collection = "orders"
    account_id = "123"
    consumerKey = "123"
    consumerSecret = "123"
    tokenId = "123"
    tokenSecret = "123"
    sb_url = ""
    ns_rest_api_endpoint = ""

    logging_queue_url = "https://sqs.us-east-1.amazonaws.com/778359441486/dev-base-logging-queue"
    log_level = "Info"
    gateway_url = "https://127.0.0.0:8000"
    sns_endpoint = 'arn:aws:sns:us-east-1:778359441486:dev-BASEAPI-CustomerOrder-Upsert-notifications'
    sqs_url = "https://sqs.us-east-1.amazonaws.com/778359441486/testing-invoice-notifications-delete-me-mark"


    url = constants.EMPTY

    secrets_service = None

    def __init__(self, app_name):
        self.application_name = app_name
        self._configure()
        return

    def _configure(self):
        self._configure_logging()
        self.load_env()
        #self.logger.info("Database credentials read from Secrets: {}.".format(self.secrets_name))
        # self.url = 'mongodb://' + self.mongo_user + ":" + self.mongo_passwd + "@" \
        #            + self.mongo_host + ":" + str( self.mongo_port) + "/?replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
        # self.mongo_database = self.mongo_database
        # self.mongo_collection = self.mongo_collection
        # self.mongo_user = self.mongo_user

        return

    def _configure_logging(self):
        try:
            self.logger = IhmBaseLogger(self.application_name, self.logging_queue_url, self.log_level, component="order-api", region="us-east-1")
        except Exception as e:
            print("Error occurred configuring Application Logging. {}".format(e))
            raise e

    def get_logger(self):
        return self.logger

    def load_secrets(self):
        try:
            self.secrets_service = SecretsManagerService(self.secrets_name, self.region)
            dict = self.secrets_service.get_dict()
            self.account_id = dict[constants.ACCOUNT_ID]
            self.consumerSecret = dict[constants.CONSUMER_SECRET]
            self.consumerKey = dict[constants.CONSUMER_KEY]
            self.tokenId = dict[constants.TOKEN_ID]
            self.tokenSecret = dict[constants.TOKEN_SECRET]
            self.sb_url = dict[constants.NS_SANDBOX_URL]
            self.ns_rest_api_endpoint = dict[constants.NS_REST_API_ENDPOINT]

            print("App Credentials loaded from SecretsManager: {}".format(self.secrets_name))
        except SecretsManagerConfigurationException as smce:
            self.logger.error("SecretsManager error: {} -- die".format(smce))
            raise smce
        return

    def load_env(self):
        temp = constants.EMPTY
        temp = os.getenv(constants.REGION)
        if temp is not None and temp != constants.EMPTY:
            self.region = temp

        temp = constants.EMPTY
        temp = os.getenv(constants.SECRETS_NAME)
        if temp is not None and temp != constants.EMPTY:
            self.secrets_name = temp
        self.load_secrets()

        temp = constants.EMPTY
        temp = os.getenv(constants.LOG_QUEUE_URL)
        if temp is not None and temp != constants.EMPTY:
            self.logging_queue_url = temp


        temp = constants.EMPTY
        temp = os.getenv(constants.SQS_URL)
        if temp is not None and temp != constants.EMPTY:
            self.sqs_url = temp

        temp = constants.EMPTY
        temp = os.getenv(constants.LOG_LEVEL)
        if temp is not None and temp != constants.EMPTY:
            self.log_level = temp

        temp = constants.EMPTY
        temp = os.getenv(constants.ENV)
        if temp is not None and temp != constants.EMPTY:
            self.env = temp
        print("Current ENV is: {}\n".format(self.env))
        return

    def toJSON(self):
        """
        Returns a JSON dictionary object of this LogEntry
        :return:
        """
        return self.__dict__
