from pymongo import MongoClient

from api.config import app_constants, AppSettings
from api.services.IhmBaseLogger import IhmBaseLogger
from api.exceptions.DataAccessError import DataAccessError
from api.data_persistence.iDataService import iDataService
# from api.models.invoice_models import Invoice
from api.models.invoice_models import InvoiceDetailed
from api.models.DataOperationResult import DataOperationResult


class InvoiceDocDbDataService(iDataService):
    """
    DbService provides Database connectivity and operational methods used to
    read and persist data to the Database.
    """
    config = None
    logger = None
    constants = app_constants
    url = None
    dbName: str = ""
    dbCollection: str = ""
    settings = None
    db_conn = None

    def __init__(self, settings: AppSettings = None):
        self.settings = settings
        self.logger = IhmBaseLogger.get_logger(settings)
        self.url = 'mongodb://' + settings.dbUser + ":" + settings.dbPasswd.get_secret_value() + "@" \
                   + settings.dbHost + ":" + str(settings.dbPort) + "/?replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
        self.dbCollection = settings.dbCollection
        self.dbName = settings.dbName
        return

    def __build_db_uri(self):
        uri = self.url
        return uri

    def get_connection(self):
        if self.db_conn is None:
            self.db_conn = self.open()
        return self.db_conn

    def open(self):
        db_client = MongoClient(self.__build_db_uri())
        return db_client

    def close(self, conn):
        conn.close()
        return True

    def save(self, invoice: InvoiceDetailed):
        client = None
        try:
            # Persist Order to database
            client = self.get_connection()
            db = client.get_database(self.dbName)
            collection = db.get_collection(self.dbCollection)
            response = collection.insert_one(invoice.dict())
            # self.close(client)
            if response is None:
                self.logger.error(self.settings.api_model_name + ".id {} insert failed. Response: {}".format(invoice.id, response))
                return response
            else:
                # print("Insert success...")
                # response['_id'] = str(response['_id'])
                self.logger.info("Created new document " + self.constants.RTM_RESOURCE_NAME + ".id {} ".format(invoice.id))
                print("Created new document " + self.constants.RTM_RESOURCE_NAME + ".id {} ".format(invoice.id))
            return response
        except Exception as e:
            if client is not None:
                self.close(client)
            message = "save() - Exception occurred {}".format(e)
            raise DataAccessError(message)

    # def delete_by_id(self, _id):
    #     client = self.get_connection()
    #     try:
    #         db = client.get_database(self.config.mongo_database)
    #         collection = db.get_collection(self.config.mongo_collection)
    #         print("Deleting "+self.settings.api_model_name+".id = {}".format(_id))
    #         result = collection.delete_one({"id": _id})
    #         print("Delete result = {}".format(str(result)))
    #         if result is not None:
    #             print("Deleted "+self.settings.api_model_name+".id = {}".format(_id))
    #     except Exception as e:
    #         if client is not None:
    #             self.close(client)
    #         self.logger.error("Error occurred deleting "+self.settings.id+".id = {}".format(_id))
    #         return {"message": "FAILURE"}

    def get_all(self):
        # return query of orders which are modified after the last modified date
        results = []
        client = None
        try:
            client = self.get_connection()
            db = client.get_database(self.dbName)
            collection = db.get_collection(self.dbCollection)
            cursor = collection.find()
            if cursor.count() != 0:
                for doc in cursor:
                    objId = str(doc["_id"])
                    doc["_id"] = objId
                    results.append(doc)
            # self.close(client)
        except Exception as e:
            if client is not None:
                self.close(client)
            message = "get_all() - Exception occurred {}".format(e)
            raise DataAccessError(message)
        return results

    def get_by_id(self, _id, loadInactive: bool = False):
        # Get Order by id
        client = None
        try:
            client = self.get_connection()
            db = client.get_database(self.dbName)
            collection = db.get_collection(self.dbCollection)
            # self.logger.info("Searching for Order.id: {}".format(_id))
            result = collection.find_one({'id': _id})
            # self.logger.debug("Order = {}".format(result))
            if result is not None:
                result['_id'] = str(result['_id'])
                # print("Result = {}".format(result))
            else:
                result = None
            # self.close(client)
            return result
        except Exception as e:
            if client is not None:
                self.close(client)
            message = "get_by_id {} - Exception occurred {}".format(_id, e)
            raise DataAccessError(message)

    def query(self, query):
        pass

    # def query(self, query: RevenueTypeMapQuery):
    #     conditions = []
    #
    #     if query.agency != constants.EMPTY:
    #         if query.agency == "*":
    #             conditions.append({"agency": {"$ne": None}})
    #         else:
    #             conditions.append({"agency": {"$eq": query.agency}})
    #
    #     if query.customerOrderType != constants.EMPTY:
    #         conditions.append({"customerOrderType": {"$eq": query.customerOrderType}})
    #     if query.dealType != constants.EMPTY:
    #         conditions.append({"dealType": {"$eq": query.dealType}})
    #
    #     if query.lineOfBusiness != constants.EMPTY:
    #         conditions.append({"lineOfBusiness": {"$eq": query.lineOfBusiness}})
    #
    #     if query.politicalSpend != constants.EMPTY:
    #         if query.politicalSpend == 'true' or query.politicalSpend == 'True':
    #             conditions.append({"politicalSpend": {"$eq": 'true'}})
    #         else:
    #             conditions.append({"politicalSpend": {"$eq": 'false'}})
    #
    #     if query.product_id != constants.EMPTY:
    #         conditions.append({"product.id": {"$eq": query.product_id}})
    #
    #     db_query = {"$and", conditions}
    #     self.logger.debug("Querying Database for conditions: {}".format(str(db_query)))
    #     results = []
    #     client = None
    #     try:
    #         client = self.open()
    #         db = client.get_database(self.mongo_database)
    #         collection = db.get_collection(self.mongo_collection)
    #         cursor = collection.find(db_query)
    #         if cursor.count() != 0:
    #             for doc in cursor:
    #                 objId = str(doc["_id"])
    #                 doc["_id"] = objId
    #                 results.append(doc)
    #         self.close(client)
    #     except Exception as e:
    #         if client is not None:
    #             self.close(client)
    #         message = "query() - Exception occurred {}".format(e)
    #         raise DataAccessError(message)
    #     return results

    def delete_by_id(self, _id) -> DataOperationResult:
        client = None
        result = DataOperationResult()
        try:
            client = self.get_connection()
            db = client.get_database(self.dbName)
            collection = db.get_collection(self.dbCollection)
            # self.logger.info("Searching for Order.id: {}".format(_id))
            response = collection.delete_one({'id': _id})
            # self.logger.debug("Order = {}".format(result))
            if response is not None:
                if response.acknowledged:
                    result.status = self.constants.SUCCESS
                    result.message = "Deleted " + self.constants.RTM_RESOURCE_NAME + ".id: " + str(_id)
                # print("Result = {}".format(result))
            else:
                result.status = self.constants.FAILURE
                result.message = "Could not delete " + self.constants.RTM_RESOURCE_NAME + ".id: " + str(_id)
            # self.close(client)
            return result
        except Exception as e:
            if client is not None:
                self.close(client)
            message = "delete_by_id() - ID: {} - Exception occurred {}".format(_id, e)
            raise DataAccessError(message)

    """
    def page_orders(self, page_request):
        client = self.open()
        try:
            # Calculate number of documents to skip
            skip_count = page_request.page_size * (page_request.page_num - 1)
            db = client.get_database(self.mongo_database)
            collection = db.get_collection(self.mongo_collection)
            # Skip and limit
            cursor = collection.find().skip(skip_count).limit(page_request.page_size)

            # Return documents
            return [x for x in cursor]
        except Exception as e:
            return {}
    """
