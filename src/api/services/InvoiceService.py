import json
import copy
import datetime
from fastapi import HTTPException

from api.data_persistence.InvoiceDocDbDataService import InvoiceDocDbDataService
# from api.models.pagination import PagedResponse
# from fastapi_pagination import PaginationParams
from api.config.AppSettings import AppSettings
from api.services.IhmBaseLogger import IhmBaseLogger
import jsonpatch
from api.services.NotificationService import NotificationService
from api.exceptions.NotificationError import NotificationError
from api.config import app_constants
from api.exceptions.ItemExistsException import DataItemExistsException
from api.exceptions.PatchException import PatchException
from api.exceptions.DataNotFoundException import DataNotFoundException
# from api.models.invoice_models import Invoice
from api.models.invoice_models import InvoiceDetailed


class InvoiceService():
    logger = None
    db_service = None
    notification_service = NotificationService = None
    constants = app_constants
    settings = None
    FORMAT_DETAIL = "detail"
    FORMAT_SUMMARY = "summary"
    FORMAT_STANDARD = "standard"
    NOTIFICATION_SCOPE = "BASEAPI"
    NOTIFICATION_RESOURCE_TYPE = "Invoice"
    NOTIFICATION_EVENT_TYPE_UPDATE = "Update"
    NOTIFICATION_EVENT_TYPE_DELETE = "Delete"
    NOTIFICATION_EVENT_TYPE_ADJUSTMENT_APPLIED = "AdjustmentApplied"
    SNS_TOPIC_SUFFIX = "notifications"
    SNS_TOPIC_ARN_FORMAT = "arn:aws:sns:us-east-1:{accountId}:{topicName}"
    actor = "not provided"

    def __init__(self, settings: AppSettings = None):
        self.settings = settings
        self.logger = IhmBaseLogger.get_logger(settings)
        self.db_service = InvoiceDocDbDataService(settings)
        self.notification_service = NotificationService(settings)

    def invoice_exists(self, _id: str):
        result = False
        invoice = self.db_service.get_by_id(_id, loadInactive=True)
        if invoice is not None:
            result=True
        return result

    def save_and_notify(self, invoice: InvoiceDetailed):
        urlForOperation = "/" + self.constants.URL_RESOURCE_NAME
        id = invoice.id
        try:
            self.logger.info("Attempting to save Invoice.ID = {}".format(id))
            if not self.invoice_exists(id):
                self.db_service.save(invoice)
                self.logger.info("Invoice.ID {} - saved.".format(id))
            else:
                raise HTTPException(status_code=409, detail="Invoice.id {} already exists.".format(id))
        except Exception as e:
            self.logger.error("Exception occurred saving Invoice {}".format(e))
            raise e
        else:  # since success now send notification
            try:
                self.logger.info("sending notification of successful {} for {} ID = {}".format(self.constants.POST, self.constants.RTM_RESOURCE_NAME, id))
                self.notification_service.send_message(self.constants.POST, urlForOperation, id, self.constants.RTM_RESOURCE_NAME, self.actor, invoice.isAdjustmentInvoice)
                self.logger.info("successfully sent notification of {} for {} ID = {}".format(self.constants.POST, self.constants.RTM_RESOURCE_NAME, id))
            except NotificationError as ne:
                self.logger.error("Error while sending notification of successful POSTed {} with ID = {}. Error details {}".format(self.constants.RTM_RESOURCE_NAME, id, ne))
                raise
            return id

    def update_and_notify(self, _id: str, invoice: InvoiceDetailed):
        urlForOperation = "/" + self.constants.URL_RESOURCE_NAME
        try:
            self.db_service.delete_by_id(_id)
            self.db_service.save(invoice)
        except Exception as e:
            self.logger.error("Exception occurred updating Invoice.id {} -  {}".format(_id, e))
            raise e
        else:  # since success now send notification
            try:

                self.logger.info("sending notification of successful {} for {} ID = {}".format(self.constants.PUT, self.constants.RTM_RESOURCE_NAME, _id))
                self.notification_service.send_message(self.constants.POST, urlForOperation, _id, self.constants.RTM_RESOURCE_NAME, self.actor, invoice.isAdjustmentInvoice)
                self.logger.info("successfully sent notification of {} for {} ID = {}".format(self.constants.PUT, self.constants.RTM_RESOURCE_NAME, _id))
            except NotificationError as ne:
                self.logger.error("Error while sending notification of successful POSTed {} with ID = {}. Error details {}".format(self.constants.RTM_RESOURCE_NAME, _id, ne))
                raise
            return _id

    def get_by_id(self, id, format: str = app_constants.DETAILED, loadInactive: bool = False):
        result = None
        try:
            self.logger.info("Attempting to read Invoice.ID = {}".format(id))
            result = self.db_service.get_by_id(id, loadInactive)
            if format == self.constants.SUMMARY:
                result = self.build_summary(result)
            elif format == self.constants.STANDARD:
                result = self.build_standard(result)
            self.logger.info("Successfully read Invoice.ID = {}".format(id))
        except Exception as e:
            self.logger.error("Exception occurred returning Invoice.id {} - {}".format(id, e))
            raise e
        else:
            if result is None:
                # Throw 404 Not found exception
                raise DataNotFoundException("Invoice with ID = {} not found. ".format(id))
            return result

    def delete_invoice_by_id(self, id):
        result = None
        try:
            self.logger.info("Attempting to DELETE Invoice.ID = {}".format(id))
            result = self.db_service.delete_by_id(id)
            self.logger.info("Successfully deleted Invoice.ID = {}".format(id))
        except Exception as e:
            self.logger.error("Exception occurred deleting Invoice.id {} - {}".format(id, e))
            raise e
        else:
            return result

    def get_all(self, loadInactive: bool = False):
        result = None
        try:
            self.logger.info("Attempting to get all Invoice data.")
            result = self.db_service.get_all(loadInactive)
            self.logger.info("Successfully read Invoices")
        except Exception as e:
            self.logger.error("Exception occurred returning Invoice.id {} - {}".format(id, e))
            raise e
        else:
            return result

    def __prepare_patched_result(self, id, patch_list) -> InvoiceDetailed:
        original_result: dict = None
        patched_result: dict = None
        try:
            original_result = self.db_service.get_by_id(id, False)
            patched_result = original_result
        except Exception as e:
            raise PatchException("Invoice with ID = {} not found, due to error {}. ".format(id, str(e)))
        else:
            if original_result is None:
                # Throw 404 Not found exception
                raise DataNotFoundException("Invoice with ID = {} not found. ".format(id))
        ## build patch operations and validate them
        count = 1
        # apply to one patch at a time
        for patch_item in patch_list:
            list = []  # empty the shell for each item to comply with patch operation
            try:
                # create patch operation with all operations up to this point.
                list.append(patch_item.dict())
                patch = jsonpatch.JsonPatch(list)
                self.logger.info(
                    "Step {} - Applying patch  {} -  to Invoice {} ".format(str(count), patch, patched_result["id"]))
                patched_result = patch.apply(patched_result)
            except (jsonpatch.JsonPatchException or jsonpatch.JsonPointerException)as jpe:
                print("JSONPatchException {}".format(jpe))
                self.logger.error("JsonPatch Exception: {} - Path = {}".format(jpe, patch_item))
                self.logger.error("PATCH Step {} failed for Invoice ID: {} - Patch_Path - {}".format(str(count), id,
                                                                                                     patch_item.dict()[
                                                                                                         "path"]))
                raise PatchException("PATCH Step {} failed for Invoice ID: {} - Patch_Path: {}.  Due to error: {}".format(str(count),
                                                                                                                          id,
                                                                                                                          patch_item.dict()["path"],
                                                                                                                          str(jpe)))
            else:
                self.logger.info("Invoice ID: {} - Step {} - PATCH applied.".format(patched_result["id"], str(count)))
                count += 1
        patched_revenue_type_map = InvoiceDetailed.parse_obj(patched_result)
        return patched_revenue_type_map

    def patch_and_notify(self, id, patch_list):
        # save and notify very similar to a save except logging and notification type
        urlForOperation = "/" + self.constants.URL_RESOURCE_NAME
        try:
            patched_result = self.__prepare_patched_result(id, patch_list)
            self.logger.info("Attempting to patch Invoice. ID = {}".format(id))
            self.db_service.save_rev_type_map(patched_result)
            self.logger.info("Invoice patched. ID = {}".format(id))
        except Exception as e:
            self.logger.error("Exception occurred saving Order {}".format(e))
            raise PatchException("Patch failed due to error: {} ".format(str(e)))
        else:  # since success now send notification
            try:
                self.logger.info("sending notification of successful {} for {} ID = {}".format(self.constants.PATCH,
                                                                                               self.constants.RTM_RESOURCE_NAME,
                                                                                               id))
                self.notification_service.send_message(self.constants.PATCH, urlForOperation, id,
                                                       self.constants.RTM_RESOURCE_NAME, self.actor, patched_result.isAdjustmentInvoice)
                self.logger.info("successfully sent notification of {} for {} ID = {}".format(self.constants.PATCH,
                                                                                              self.constants.RTM_RESOURCE_NAME,
                                                                                              id))
            except NotificationError as ne:
                self.logger.error(
                    "Error while sending notification of successful POSTed {} with ID = {}. Error details {}".format(
                        self.constants.RTM_RESOURCE_NAME, id, ne))
                raise
            else:  # successful notification and save, return success
                return (self.get_by_id(id, False))
                self.logger.info("Invoice ID: {} - PATCH Complete. Invoice updates persisted to database.".format(patched_result["id"]))

    # def query(self, query: RevenueTypeMapQuery, loadInactive: bool):
    #     queryResult = None
    #     try:
    #         self.logger.info("Attempting to query for a single RevenueTypeMap based on multiple conditions {}".format(query.json()))
    #         queryResult = self.db_service.query(query, loadInactive)
    #         # check if more than one returned
    #         if (len(queryResult) > 1):
    #             self.logger.error("Query conditions resulted more than one revenue type map which is not allowed. results: {} conditions {}".format(json.dumps(queryResult), query.json()))
    #             raise TooManyResultsException("No data found matching query conditions: {}".format(query.json()))
    #         # check if zero returned
    #         if (len(queryResult) < 1):
    #             self.logger.error("Query conditions resulted in no results. conditions {}".format(query.json()))
    #             raise DataNotFoundException("No data found matching query conditions: {}".format(query.json()))
    #         else:
    #             self.logger.info("Successfully retreived a single revenue type map for query: conditions {}".format(query.json()))
    #     except DataNotFoundException as dnf:
    #         raise dnf
    #     except TooManyResultsException as tmr:
    #         raise tmr
    #     except Exception as e:
    #         self.logger.error("Error.".format(str(e)))
    #         raise Exception("Error: {}".format(str(e)))
    #     else:
    #         return queryResult[0]

    def generate_sns_topic(self, notification):
        return "{env}-{scope}-{resourceType}-{eventType}-{suffix}".format(
            env=self.settings.env,
            scope=notification["scope"],
            resourceType=notification["resourceType"],
            eventType=notification["eventType"],
            suffix=self.SNS_TOPIC_SUFFIX)

    def send_notification(self, logger, invoice_fulfillment_id, is_update, request_tracking_id):
        self.logger.info("Begin send_notification. Tracking ID: {}".format(request_tracking_id))

        now = datetime.datetime.now()
        notification = {
            "scope": self.NOTIFICATION_SCOPE,
            "resourceType": self.NOTIFICATION_RESOURCE_TYPE,
            "eventType": None,
            "resourceID": invoice_fulfillment_id,
            "notificationSource": "{application_name}".format(application_name=self.settings.application_name),
            "timeStamp": now.isoformat(),
            "resourceLinks": [
                {
                    "linkType": "api",
                    "linkBase": self.settings.gateway_url,
                    "linkPath": "/api/v1/invoice/{invoice_fulfillment_id}".format(
                        invoice_fulfillment_id=invoice_fulfillment_id)
                }
            ]
        }
        if is_update:
            notification["eventType"] = self.NOTIFICATION_EVENT_TYPE_UPDATE
        else:
            notification["eventType"] = self.NOTIFICATION_EVENT_TYPE_DELETE

        topic_name = self.generate_sns_topic(notification)
        topic_arn = self.SNS_TOPIC_ARN_FORMAT.format(accountId=self.settings.aws_account_id,
                                                     topicName=topic_name)

        try:

            self.sns_client.get_topic_attributes(
                TopicArn=topic_arn
            )

            return self.sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(notification)
            )
        except self.sns_client.exceptions.NotFoundException as e:
            self.logger.error("Topic for notification {} is not found. Tracking ID: {}".format(
                topic_arn, request_tracking_id))
            raise Exception("Topic for notification {topicArn} is not found".format(
                topicArn=topic_arn))
        except Exception as e:
            self.logger.error("Exception occurred while topic registration {notification} is invalid "
                              + "with exception {exception}".format(notification=json.dumps(notification), exception=e),
                              request_tracking_id)
            raise Exception("Exception occurred while topic registration {notification} is invalid "
                            "with exception {exception}".format(notification=json.dumps(notification), exception=e))
        finally:
            self.logger.info("Notification sent. Tracking ID: {}".format(request_tracking_id))

    def build_summary(self, invoice_fulfillment_detailed):
        summary = copy.deepcopy(invoice_fulfillment_detailed)
        del summary["invoiceLines"]
        return summary

    def build_standard(self, invoice_fulfillment_detailed):
        standard = copy.deepcopy(invoice_fulfillment_detailed)
        for invoice_line in standard["invoiceLines"]:
            del invoice_line["fulfillments"]
        return standard
