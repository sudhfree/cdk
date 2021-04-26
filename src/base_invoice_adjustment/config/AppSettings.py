import os
from typing import Set, List, Optional, TypeVar

from pydantic import (
    ValidationError,
    validator,
    BaseModel,
    BaseSettings,
    PyObject,
    Field
)


class AppSettings(BaseSettings):
    # define the fields using pydantic settings management markings/syntax.  indicate type, the name of the field in the environment, defaults
    application_name: str
    component_name: str
    env: str
    region: str
    logging_queue_url: str
    log_level: str
    api_url: str
    api_key: str
    api_key_id: str
    s3_bucket: str
    s3_filekey: str


# class AppSettings(BaseSettings):
#     # define the fields using pydantic settings management markings/syntax.  indicate type, the name of the field in the environment, defaults
#     bia_application_name: str
#     bia_component_name: str
#     env: str
#     # secrets_name: str
#     region: str
#     logging_queue_url: str
#     log_level: str
#     api_url: str
#     api_key: str