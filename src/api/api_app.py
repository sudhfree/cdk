import os, sys, shutil
import boto3
import uvicorn
from fastapi import FastAPI, APIRouter, status, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from mangum import Mangum
from typing import List, Optional, Any
from api.services.InvoiceService import InvoiceService
from api.config.AppSettings import AppSettings
from api.services.IhmBaseLogger import IhmBaseLogger
from api.config import app_constants
from api.models.invoice_models import Invoice
from api.models.invoice_models import InvoiceDetailed
from api.exceptions.DataNotFoundException import DataNotFoundException
from api.exceptions.NotificationError import NotificationError
from api.exceptions.PatchException import PatchException
from api.exceptions.DataAccessError import DataAccessError
from api.exceptions.TooManyResultsException import TooManyResultsException
from api.models.PatchRequest import PatchRequest
from fastapi_pagination import Page, pagination_params, PaginationParams, paginate
from pydantic_kms_secrets import decrypt_kms_secrets

# initialize instance variables, environment variables etc and add them to a global context instance
handler = None
constants = app_constants
router = APIRouter()
api_app = FastAPI()
invoice_service: InvoiceService = None  # revenue_type_map service class
logger: IhmBaseLogger = None
settings: AppSettings = None



"""
revenue type map routes
"""
print("initializing")


@api_app.get("/invoice/{id}")
async def get_by_id(id: str, format: str, request: Request, loadInactive: Optional[bool] = False):
    url_resource_name = constants.RTM_RESOURCE_NAME
    urlForOperation = "/" + constants.URL_RESOURCE_NAME + "/{id}"
    """
    temporary showing of secrets to show it in the app
    """
    # print("decrypted secret from build"+settings.secret_created_in_build.get_secret_value())
    # print("decrypted manual secret: " + str(settings.secret_manually_created.get_secret_value()))
    try:
        result = invoice_service.get_by_id(id, format, loadInactive)
        return JSONResponse(content=jsonable_encoder(result), media_type="application/json")
    except DataNotFoundException as dnf:
        raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get failed, see logs for details")


@api_app.get("/invoice", response_model=Page[Invoice], dependencies=[Depends(pagination_params)])
async def get(loadInactive: Optional[bool] = False, params: PaginationParams = Depends()) -> Any:
    url_resource_name = constants.RTM_RESOURCE_NAME + 's'
    urlForOperation = "/" + constants.URL_RESOURCE_NAME
    # revenue_type_maps: RevenueTypeMaps = None
    try:
        unpagedResult = invoice_service.get_all(loadInactive)
        pagedResult = paginate(unpagedResult, params)
    except DataNotFoundException as dnf:
        raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Get failed, see logs for details")
    else:
        return pagedResult


@api_app.post("/invoice", status_code=status.HTTP_200_OK)
async def post(invoice: InvoiceDetailed):
    # log start, send, log result, send notification
    print("arrived at post")
    try:
        id = invoice_service.save_and_notify(invoice)
    except DataAccessError as dae:
        raise HTTPException(status_code=500, detail="Insert failed, see logs for details")
    except NotificationError as ne:
        raise HTTPException(status_code=500, detail="Notification after update failed")
    else:  # return success should create an object.
        return {"status": constants.SUCCESS, constants.RTM_RESOURCE_NAME: id}


@api_app.put("/invoice/{id}", status_code=status.HTTP_200_OK)
async def put_invoice(id: str, invoice: InvoiceDetailed):
    try:
        invoice_service.update_and_notify(id, invoice)
        return {"status": constants.SUCCESS, constants.RTM_RESOURCE_NAME: id}
    except DataAccessError as dae:
        raise HTTPException(status_code=500, detail="Update failed, see logs for details")
    except NotificationError as ne:
        raise HTTPException(status_code=500, detail="Notification after update failed")


@api_app.patch("/invoice/{id}", status_code=status.HTTP_200_OK)
def patch_and_notify(id: str, patch_list: List[PatchRequest]):
    invoice: Invoice = None
    try:
        rev_type_map = invoice_service.patch(id, patch_list)
    except DataNotFoundException as dnf:
        raise HTTPException(status_code=404, detail="Item not found")
    except NotificationError as nfe:
        raise HTTPException(status_code=500, detail="Notification after update failed")
    except PatchException as pe:
        raise HTTPException(status_code=500, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Patch failed due to system failure.  See logs for details")
    else:
        return rev_type_map


@api_app.delete("/invoice/{id}", status_code=status.HTTP_200_OK)
def delete_order_by_id(id: str):
    # delete an Order by ID
    response = invoice_service.delete_invoice_by_id(id)
    logger.info("Invoice Delete response: {}".format(response))
    # notification_service.send_message(constants.DELETE, '/order', id, constants.ADPLUS)
    return {"status": constants.SUCCESS, "message": "Invoice.id={} deleted.".format(id)}


# @api_app.post("/invoice/query", status_code=status.HTTP_200_OK)
# def query(query: RevenueTypeMapQuery, loadInactive: Optional[bool] = False):
#     rev_type_map: RevenueTypeMap = None
#     try:
#         rev_type_map = rtm_service.query(query, loadInactive)
#     except DataNotFoundException as dnf:
#         raise HTTPException(status_code=404, detail="Query produced no results")
#     except TooManyResultsException as tmr:
#         raise HTTPException(status_code=500, detail="Too many results returned, only one Rev Type Map result is allowed")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Query failed due to system failure.  See logs for details")
#     else:
#         return rev_type_map


def build_s3_keyfile_name():
    file_name = settings.application_name + "/" + settings.env + "/config/app.env"
    return file_name


def load_settings_from_s3(_settings: AppSettings):
    s3_settings: AppSettings = None
    try:
        s3 = boto3.resource('s3')
        print("Reading file from S3 Bucket: {}  - FileKey: {}".format(_settings.s3_bucket, _settings.s3_filekey))
        s3.Bucket(_settings.s3_bucket).download_file(_settings.s3_filekey, settings_file)
        print("S3 Read completed.")
        s3_settings = AppSettings(_env_file=settings_file, _env_file_encoding="utf-8")
        print("Settings updated from S3.")
        print("Current S3 Settings: {}".format(str(s3_settings.__dict__)))
        return s3_settings
    except Exception as e:
        print("Exception occurred copying S3 config file! {}".format(e))
    return None


execution_mode = os.getenv('execution_mode')
if execution_mode == "local":
    if __name__ == '__main__':
        settings_file: str = "config/dev.app.env"
        # hardwire to dev for now
        currentdir = os.path.dirname(os.path.realpath(__file__))
        parentdir = os.path.dirname(currentdir)
        sys.path.append(parentdir)
        import src.api.config.AppSettings as _settings

        # settings = decrypt_kms_secrets(AppSettings(_env_file='config/dev.app.env', _env_file_encoding='utf-8'))
        settings = AppSettings(_env_file=settings_file, _env_file_encoding='utf-8')
        settings = load_settings_from_s3(settings)
        # settings = decrypt_kms_secrets(AppSettings())
        logger = IhmBaseLogger.get_logger(settings)
        logger.info("Starting up Invoice API in local mode")
        invoice_service = InvoiceService(settings)
        uvicorn.run(api_app, host='127.0.0.1', port=8001)
else:
    settings_file: str = "/invoice_api/api/config/app.env"
    print("running in Lambda or Fargate")
    # configure
    # settings = decrypt_kms_secrets(AppSettings())  # environment all required fields are populated via env or file
    # settings = AppSettings()
    print("Loading initial settings file: {}".format(settings_file))
    settings = AppSettings(_env_file=settings_file, _env_file_encoding="utf-8")
    settings = load_settings_from_s3(settings)
    invoice_service = InvoiceService(settings)
    logger = IhmBaseLogger.get_logger(settings)
    logger.info("Staring up the Invoice API in deployed mode")
    handler = Mangum(api_app)
