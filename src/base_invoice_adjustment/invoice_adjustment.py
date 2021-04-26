import boto3
import requests
from datetime import datetime
import json
import ast
from json import JSONEncoder
from types import SimpleNamespace
from config.AppSettings import AppSettings
from services.secret_service import SecretsManagerService, SecretsManagerConfigurationException
from services.IhmBaseLogger import IhmBaseLogger


app_name = "ihmbase-ns-invoice-notifier"
settings: AppSettings = None
settings_file: str = "config/app.env"
settings_file2: str = "/tmp/app2.env"

print("Loading initial settings file: {}".format(settings_file))
settings = AppSettings(_env_file=settings_file, _env_file_encoding="utf-8")
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


def get_invoice(invoice_id):
    global logger
    global settings
    invoice = None
    try:
        # url = build_get_invoice_url_request(notification)
        logger.info("Calling Invoice API to get Invoice.id: {}".format(invoice_id))
        print("Callling Ivoice API {} to get Invoice.id = {}".format(settings.api_url, invoice_id))
        headers = {'x-api-key': settings.api_key}
        print("Invoice GET Request is: {}", settings.api_url + "/invoice/" + str(invoice_id)+"?format=detail")
        invoice_response = requests.get(settings.api_url + "/invoice/" + str(invoice_id)+"?format=detail", headers=headers)
        if invoice_response.status_code == 200:
            invoice = invoice_response.json()
            print("Read invoice: {}".format(invoice))
            logger.info("Read Invoice.id = {}".format(invoice["id"]))
        else:
            print("GET Invoice status: {}".format(invoice_response.status_code))
    except Exception as e:
        logger.error("Exception calling Invoice API: {}".format(e))
        raise e
    return invoice


def put_invoice(updated_invoice):
    global logger
    global settings
    status_code = 0
    try:
        # url = build_get_invoice_url_request(notification)
        logger.info("Calling Invoice API to update Invoice.id: {}".format(updated_invoice))
        headers = {'x-api-key': settings.api_key}
        invoice_response = requests.put(settings.api_url + "/invoice/" + str(updated_invoice["id"]), headers=headers, json=updated_invoice)
        if invoice_response.status_code == 200:
            status_code = invoice_response.status_code
            print("Invoice.id = {} updated for Adjustment.".format(updated_invoice["id"]))
            logger.info("Invoice.id = {} updated for Adjustment.".format(updated_invoice["id"]))
        else:
            print("PUT Invoice FAILED. status: {} - Response: {}".format(invoice_response.status_code, str(invoice_response)))
            logger.error("PUT Invoice FAILED. status: {} - Response: {}".format(invoice_response.status_code, str(invoice_response)))
    except Exception as e:
        logger.error("Exception calling Invoice API: {}".format(e))
        raise e
    return status_code


def update_parent_invoice(invoice, adj_invoice_id):
    invoice["isAdjusted"] = True
    if invoice["adjustmentInvoicesAppliedToThisInvoice"] is None:
        invoice["adjustmentInvoicesAppliedToThisInvoice"] = []
    invoice["adjustmentInvoicesAppliedToThisInvoice"].append(adj_invoice_id)
    invoice["lastModifiedDate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    status = put_invoice(invoice)
    if status == 200:
        print("Invoice.id {} Adjusted.".format(invoice["id"]))
        logger.info("Invoice.id {} Adjusted.".format(invoice["id"]))
    else:
        print("Failed to update Invoice.id = {}.".format(invoice["id"]))
        logger.error("Failed to update Invoice.id = {}.".format(invoice["id"]))
    return


def update_adjusted_invoices(adj_invoice):
    global logger
    for invoice_id in adj_invoice["invoicesAdjustedByThisInvoice"]:
        parent_invoice = get_invoice(invoice_id)
        if "_id" in parent_invoice.keys():
            print("Deleting key _id from invoice.")
            del parent_invoice["_id"]
        logger.info("Updating Invoice.id {}.".format(invoice_id))
        update_parent_invoice(parent_invoice, adj_invoice["id"])
    return


def process_adjustment_invoice(adj_invoice):
    # update Original/Parent Invoice
    update_adjusted_invoices(adj_invoice)
    return

def build_s3_keyfile_name():

    file_name = settings.application_name + "/" + settings.env + "/config/app.env"
    return file_name

def load_settings_from_s3(_settings: AppSettings):
    s3_settings: AppSettings = None
    try:
        s3 = boto3.resource('s3')
        print("Reading file from S3 Bucket: {}  - FileKey: {}".format(_settings.s3_bucket, _settings.s3_filekey))
        s3.Bucket(_settings.s3_bucket).download_file(_settings.s3_filekey, settings_file2)
        #s3.download_file(_settings.s3_bucket, _settings.s3_filekey, settings_file2)
        print("S3 Read completed.")
        s3_settings = AppSettings(_env_file=settings_file2, _env_file_encoding="utf-8")
        print("Settings updated from S3. {}".format(s3_settings))
        return s3_settings
    except Exception as e:
        print("Exception occurred copying S3 config file! {}".format(e))
    return None


def lambda_handler(event, context):
    global logger
    global settings
    status_msg = "FAILURE"
    print("Event = {}".format(event))
    event_notification = event['Records'][0]['body']

    # settings = AppSettings(_env_file=settings_file, _env_file_encoding="utf-8")
    #settings = load_settings_from_s3(settings)

    invoice_get_url = ""
    data = None
    if event_notification:
        print("Notification: {}".format(json.dumps(event_notification)))
        logger.info("Invoice notification received. {}".format(event_notification))
        # data = json.loads(event_notification, object_hook=lambda d: SimpleNamespace(**d))
        data = ast.literal_eval(event_notification)
        print("Notification Object: {}".format(str(data)))
        try:
            # call Invoice-API to get the invoice object
            invoice = get_invoice(data["id"])

            # check if Invoice isAdjustement = true
            if invoice["isAdjustmentInvoice"] is True:
                process_adjustment_invoice(invoice)

            # update parent invoice and recursively check other parents.
        except SecretsManagerConfigurationException as e:
            logger.error("Error initializing SecretsManagerService: {}".format(e))
            raise e
        except Exception as e:
            print("Exception during Invoice Adjustment:  {}".format(e))
            logger.error("Exception during Invoice Adjustment: {}".format(e))
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
