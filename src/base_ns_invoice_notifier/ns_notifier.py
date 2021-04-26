import requests
import oauthlib.oauth1
import json
import ast
from json import JSONEncoder
from types import SimpleNamespace
from config.AppSettings import AppSettings
from services.secret_service import SecretsManagerService, SecretsManagerConfigurationException
from services.IhmBaseLogger import IhmBaseLogger
from services.netSuiteService import NetSuiteService
from models.notification import NSuiteNotification, NotificationEncoder

app_name = "ihmbase-ns-invoice-notifier"


settings = AppSettings(_env_file="config/app.env", _env_file_encoding="utf-8")
print("AppSettings: {}".format(str(settings)))

logger = IhmBaseLogger(appSettings=settings)
if logger is not None:
    print("Logger initialized.")


# def print_response(res):
#     print('HTTP/1.1 {status_code}: {body}'.format(
#         status_code=res.status_code,
#         # headers='\n'.join('{}: {}'.format(k, v) for k, v in res.headers.items()),
#         body=res.content,
#     ))


def build_get_invoice_url_request(notification):
    url = notification.resourceLinks[0].linkBase
    url += notification.resourceLinks[0].linkPath
    url += "?format=summary"
    print("Invoice-API URL: {}".format(url))
    return url


def get_invoice(notification):
    invoice = None
    try:
        url = build_get_invoice_url_request(notification)
        invoice_response = requests.get(url)
        if invoice_response.status_code == 200:
            invoice = invoice_response.json()
        else:
            print("GET Invoice status: {}".format(invoice_response.status_code))
    except Exception as e:
        raise e
    return invoice


def lambda_handler(event, context):
    global logger
    status_msg = "FAILURE"
    print("Event = {}".format(event))
    event_notification = event['Records'][0]['body']
    invoice_get_url = ""
    data = None
    if event_notification:
        #event_notification = event_notification.replace("\'", "\"")
        #print("Event Notification.id = {}".format(event_notification["id"]))
        print("Notification: {}".format(json.dumps(event_notification)))
        logger.info("Invoice notification received. {}".format(event_notification))
        #data = json.loads(event_notification, object_hook=lambda d: SimpleNamespace(**d))
        data = ast.literal_eval(event_notification)
        print("Data Notification Object: {}".format(str(data)))
        print("Data.id = {}".format(data["id"]))

        # TODO: going to comment out call to Invoice-API to read the invoice info. Only need recoureId from
        #       event_notification. Eventually we will need to call Invoice-API when NS Beta Aggreement is signed
        #       and the lambda will call NS REST Services when Record Query feature is enabled.
        # call Invoice-API to get the invoice object
        #invoice = get_invoice(json.loads(event_notification, object_hook=lambda d: SimpleNamespace(**d)))
        #print("ID: {}".format(invoice['id']))
        #print("NetSuite InternalID: {}".format(invoice['netsuite-internal-id']))

        ns_notification = NSuiteNotification()
        # ns_notification.args["tranid"] = invoice["id"]
        #ns_notification.args["tranid"] = data.resourceID
        ns_notification.args["tranid"] = data["id"]
        print("NS Notification = {}".format(NotificationEncoder().encode(ns_notification)))

        try:
            ns = NetSuiteService(settings, logger)
            status_msg = ns.send_invoice_update(ns_notification)

        except SecretsManagerConfigurationException as e:
            logger.error("Error initializing SecretsManagerService: {}".format(e))
            raise e
        except Exception as e:
            print("Exception sending NS Notification: {}".format(e))
            logger.error("Exception sending NS Notification: {}".format(e))
            raise e
    else:
        print("No valid Invoice notification found in Event.")
        logger.error("No valid Invoice notification found in Event: {}".format(event))
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": status_msg
    }
