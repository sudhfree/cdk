from services.secret_service import SecretsManagerService
from services.IhmBaseLogger import IhmBaseLogger
import requests
import json
from requests_oauthlib import OAuth1
import oauthlib.oauth1
from config import app_constants as constants
from models.notification import NSuiteNotification, NotificationEncoder
from config.AppSettings import AppSettings
from services.IhmBaseLogger import IhmBaseLogger


class NetSuiteService:
    settings: AppSettings = None
    logger: IhmBaseLogger = None
    secretService: SecretsManagerService = None

    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = IhmBaseLogger.get_logger(self.settings)
        if logger is not None:
            print("Logger initialized.")
        self.secretService = SecretsManagerService(settings.secrets_name, settings.region)
        if self.secretService is not None:
            print("Secrets initialized.")
            self.secrets = self.secretService.get_dict()
        return

    def build_ns_request_url(self) -> str:
        url = self.secrets["host"]+"/app/site/hosting/restlet.nl?script="+self.secrets["scriptId"]+"&deploy="+self.secrets["deployId"]
        print("NS URL: {}".format(url))
        return url

    def send_invoice_update(self, notification):
        url = self.build_ns_request_url()
        # print("Url: {}".format(url))
        # url = "https://4024115-sb2.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=customscript_ihm_rl_nse_module_api&deploy=customdeploy_ihm_rl_nse_module_api"
        # print("HardCoded URL: {}".format(url))

        oauth = OAuth1(self.secrets["consumerKey"],
                       client_secret=self.secrets['consumerSecret'],
                       resource_owner_key=self.secrets["tokenId"],
                       resource_owner_secret=self.secrets["tokenSecret"],
                       realm=self.secrets["accountId"],
                       signature_method="HMAC-SHA1",
                       signature_type='auth_header'
                       )
        if oauth:
            print("OAuthSession Auth initialized.")
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Cache-Control"] = "no-cache"
        headers["Accept"] = "*/*"
        headers["Connection"] = "keep-alive"
        headers["Accept-Encoding"] = "gzip, deflate, br"
        # headers["Cookie"] = "lastUser="+self.secrets["accountId"]+"_7455789_1110; NS_ROUTING_VERSION=LAGGING"
        headers["Cookie"] = "lastUser=4024115_SB2_7455789_1110; NS_ROUTING_VERSION=LAGGING"
        payload = NotificationEncoder().encode(notification)
        json_body = json.dumps(payload)

        print("Headers: {}".format(headers))
        print("Payload is: {}".format(str(payload)))
        response = requests.post(url, auth=oauth, headers=headers, data=payload)
        print("Response status: {}".format(str(response.status_code)))
        if response.status_code != 200:
            print("Error Status: {} -- Body: {}".format(str(response.status_code), response.content))
            self.logger.error("Error sending NS Notification for Invoice {}: Response Code: {} -- Body: {}".format(notification.args["tranid"], str(response.status_code), str(response.content)))
            return constants.FAILURE
        else:
            rsp_dict = response.json()
            if rsp_dict is not None and "error" in rsp_dict and rsp_dict["error"] is False:
                print("Response success: {}".format(str(rsp_dict)))
                self.logger.info("Successfully updated Invoice {} in NS.".format(notification.args["tranid"]))
                return constants.SUCCESS
            else:
                self.logger.error("Error sending NS Notification for Invoice {}: Response Code: {} -- Body: {}".format(notification.args["tranid"], str(response.status_code), str(response.content)))
                return constants.FAILURE

