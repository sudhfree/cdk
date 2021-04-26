import os
from typing import Set, List, Optional, TypeVar
import pydantic_kms_secrets
import base64
import boto3


from pydantic import (
    ValidationError,
    validator,
    BaseModel,
    BaseSettings,
    PyObject,
    Field
)
from pydantic_kms_secrets import KMSSecretStr


class AppSettings(BaseSettings):
    #define the fields using pydantic settings management markings/syntax.  indicate type, the name of the field in the environment, defaults
    secrets_kms_key_id: str
    application_name: str
    component_name: str
    aws_account_id: str
    env: str
    region: str
    logging_queue_url: str
    log_level: str
    sns_endpoint: str
    adjustment_queue_url: str
    #rev_type_map_table: str
    gateway_url: str #used to construct notifications that require the URL to get the resource.
    s3_bucket: str
    s3_filekey: str
    dbHost: str
    dbPort: str
    dbName: str
    dbCollection: str
    dbUser: str
    dbPasswd: KMSSecretStr

    """
    manual encryption via command line utility, result in .env file
    pks -k ec983175-5e97-414a-bd02-ae8cd60f8c36 -v secretValue -e
    """
    secret_manually_created: Optional[KMSSecretStr]
    """
    sucks but this function is required during the build to compensate for the default behavior of pydantic_kms_secrets to mask secrets in dict().
    we need the values encrypted (or rather not decrypted) in a dict so we can set the environment values in the deployments for runtime access
    so this function does that.  if you create the instance without decrypt then executing this function will give you the undecrypted dictionary.
    if you create the instance with decrypt then executing this function will give you decrypted values in a dict.  (plus all the normal values)
    """
    def get_dict(self)->dict:
        """if the Settings has been decrypted the values will be unencrypted, otherwise values in dictionary
        are encrypted the code is unchanged"""
        kmsprefix = 'KMSSecretStr'
        newValue: str
        initialValue: str
        newDict = {'starter_bogus':'bogus'}
        for key in self.dict():
            value = getattr(self, key, None)
            if(type(value) is pydantic_kms_secrets.pydantic.KMSSecretStr):
                value = getattr(self, key, None).get_secret_value()
            newDict[str(key)]=str(value)
        newDict.pop("starter_bogus",None)
        return(newDict)
    """
    sucks but this function is required to encrypt during the build.  Items created during build must be optional and get set
    after the class is initialized by calling this function then setting the value.  
    """
    def encrypt(self, variableToEncrypt:str):
        session = boto3.session.Session()
        client = session.client('kms')
        # ciphertext = client.encrypt(
        #     KeyId=self.secrets_kms_key_id,
        #     Plaintext=bytes(variableToEncrypt,encoding='utf8'),
        # )
        response = client.encrypt(KeyId=self.secrets_kms_key_id, Plaintext=variableToEncrypt.encode())
        return base64.b64encode(response["CiphertextBlob"]).decode("utf-8")
