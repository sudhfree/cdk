from typing import Set
from typing import List, Optional


import pydantic_kms_secrets
from pydantic_kms_secrets import KMSSecretStr, decrypt_kms_secrets
from pydantic import (
    BaseModel,
    BaseSettings,
    PyObject,
    RedisDsn,
    PostgresDsn,
    Field,
)


class DeploySettings(BaseSettings):
    secrets_kms_key_id: str
    app_config_path: str
    application_name: str #name of the project.  to be used to relate all resources together.  ex: reference_data_api
    root_resource_name: str
    environment: str
    aws_resource_name_spacer: str
    env_to_domain_separator: str
    env_account: str
    env_region: str
    rootdomain: str
    zone_id: str
    cert_arn: str
    retain_table_on_stack_destroy: bool
    vpc_id: str
    privateSubNet1: str
    privateSubNet2: str
    privateSubNet3: str
    privateSubNet4: str
    task_definition_memory_limit_mib: int
    task_definition_cpu: int
    service_desired_count: int
    tag_created_by: str
    tag_created_date: str
    tag_disposition: str
    rest_api_description: str
    db_instance_type: str
    db_instance_count: int
    dbUser: str
    dbPasswd: Optional[KMSSecretStr]
    s3_bucket: str
    s3_filekey: str
    #base_invoice_adjustment ("bia") deploy settings below
    bia_app_config_path: str
    bia_application_name: str
    logging_queue_arn: str
    # base_ns_invoice_notifier ("nsnotify" prefix)
    nsnotify_app_config_path: str
    nsnotify_application_name: str
    sns_endpoint: str

    def get_dict(self)->dict:
        """if the Settings has been decrypted the values will be unencrypted, otherwise values in dictionary
        are encrypted the code is unchanged"""
        #kmsprefix = 'KMSSecretStr'
        newValue: str
        initialValue: str
        newDict = {'starter_bogus':'bogus'}
        for key in self.dict():
            value = getattr(self, key, None)
            #if(type(value) is pydantic_kms_secrets.pydantic.KMSSecretStr):
            #    value = getattr(self, key, None).get_secret_value()
            newDict[str(key)]=str(value)
        newDict.pop("starter_bogus",None)
        return(newDict)