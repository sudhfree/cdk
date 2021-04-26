import json
import os
import sys
import boto3
import botocore
from botocore.exceptions import ClientError
from pydantic_kms_secrets import decrypt_kms_secrets, encrypt

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from config.DeploySettings import DeploySettings
from src.api.config.AppSettings import AppSettings
from src.base_invoice_adjustment.config.AppSettings import AppSettings as bia_AppSettings
from src.base_ns_invoice_notifier.config.AppSettings import AppSettings as nsnotifier_AppSettings

data = None;
region = "us-east-1"
deploy_settings: DeploySettings = None
api_app_settings: AppSettings = None
secrets: dict = None
original_passwd = ""
invoice_api_key_id: str = None

deploy_settings = decrypt_kms_secrets(DeploySettings(_env_file='deploy.env', _env_file_encoding='utf-8'))
deploy_settings.s3_filekey = deploy_settings.application_name + "/" + deploy_settings.environment + "/config/app.env"
api_app_settings = AppSettings(_env_file=deploy_settings.app_config_path, _env_file_encoding='utf-8')
region = deploy_settings.env_region



def update_docdb_settings():
    global deploy_settings
    global api_app_settings
    global original_passwd
    global secrets
    client = boto3.client('docdb')
    response = client.modify_db_cluster(
        DBClusterIdentifier=secrets["dbClusterIdentifier"],
        MasterUserPassword=secrets["password"],
        ApplyImmediately=True
    )
    print("DocDb Cluster {} - Update response: {}".format(secrets["dbClusterIdentifier"], str(response)))
    return


def get_secrets(secret_name: str):
    global deploy_settings
    global original_passwd
    print("Secret Name = {}".format(secret_name))
    print("SecretName length is {}".format(str(len(secret_name))))
    index = secret_name.rfind("-")
    print("last - in secret name is {}".format(str(index)))
    secret_name = secret_name[0:index]
    print("Updated SecretName = {}".format(secret_name))

    session = boto3.session.Session()
    client = session.client("secretsmanager", region_name=region)
    try:
        print("Calling client.get_secret_value({})".format(secret_name))
        secret_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", e)
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", e)
            raise e
        elif e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Secrets Manager decrypts the secret value using the associated KMS CMK
        # Depending on whether the secret was a string or binary, only one of these fields will be populated
        if 'SecretString' in secret_response:
            secret_value = secret_response['SecretString']
            # print("SecretValue: {}\n".format(secret_value))
            dict = json.loads(secret_value)
            original_passwd = dict["password"]
            dict["password"] = deploy_settings.dbPasswd.get_secret_value()
            # print("Secrets dict: {} \n".format(str(dict)))
            client.update_secret(SecretId=secret_name, SecretString=json.dumps(dict))
        else:
            secret_value = secret_response['SecretBinary']
            dict = json.loads(secret_value)
            # print("Secret Binary  dict: {}".format(str(dict)))
    return dict


def is_dbhostname(key: str):
    if key.__contains__("hostname"):
        print("Key: {} is DB Hostname".format(key))
        return True
    return False


def is_dbSecretName(key):
    if key.__contains__("secret"):
        print("Key: {} is DB SecretName".format(key))
        return True
    return False


def is_invoice_api_key_id(key):
    if key.__contains__("usageplanapikey"):
        return True
    return False


def build_s3_keyfile_name(app_name, app_env):
    file_name = app_name + "/" + app_env + "/config/app.env"
    return file_name


def dump_dictionary(_dict: dict):
    for key in _dict:
        print("Key: {} : Value: {}".format(key, _dict[key]))


def serialize_to_s3(app_settings, s3_bucket, app_name, app_env):
    try:
        f = open("app.env", "w")
        _dict = app_settings.dict()
        for key in _dict:
            f.write("{}=\'{}\'\n".format(key, _dict[key]))
        f.close()
        s3 = boto3.resource('s3')
        print("Writing to S3. Bucket: {}  - FileKey: {}".format(s3_bucket, build_s3_keyfile_name(app_name, app_env)))
        s3.Object(s3_bucket, build_s3_keyfile_name(app_name, app_env)).put(Body=open('app.env', 'rb'))
        print("S3 Write completed.")
        os.remove("app.env")
    except Exception as e:
        print("Exception occurred serializing app.env to S3 bucket. {}".format(e))
    return

def update_api_app_settings():
    s3_keyfile = build_s3_keyfile_name(deploy_settings.application_name, deploy_settings.environment)
    print("S3 Key filename = {}".format(s3_keyfile))
    deploy_settings.s3_filekey = s3_keyfile
    api_app_settings.s3_bucket = deploy_settings.s3_bucket
    api_app_settings.s3_filekey = deploy_settings.s3_filekey
    api_app_settings.dbHost = secrets.get("host")
    api_app_settings.dbUser = secrets.get("username")
    api_app_settings.dbPasswd = secrets.get("password")
    api_app_settings.dbName = "invoices"
    api_app_settings.dbCollection = "data"
    dump_dictionary(api_app_settings.dict())
    serialize_to_s3(api_app_settings, deploy_settings.s3_bucket, deploy_settings.application_name, deploy_settings.environment)
    return



def set_api_key(settings):
    try:
        client = boto3.client('apigateway')
        response = client.get_api_key(
            apiKey=settings.api_key_id,
            includeValue=True
        )
        print("APiKey response: {}".format(response))
        settings.api_key = response["value"]
        print("API Key {} set for Invoice Adjustment lambda.".format(settings.api_key))
    except Exception as e:
        print("Exception occurred reading API Key! {}".format(e))
    return settings


def get_api_key(api_key_id):
    api_key: str = ""
    try:
        client = boto3.client('apigateway')
        response = client.get_api_key(
            apiKey=api_key_id,
            includeValue=True
        )
        print("APiKey response: {}".format(response))
        api_key = response["value"]
        print("API Key {} set for Invoice Adjustment lambda.".format(api_key))
    except Exception as e:
        print("Exception occurred reading API Key! {}".format(e))
    return api_key

def update_adjustment_env(settings: DeploySettings):
    data = {}
    try:
        print("Reading file: {}".format(settings.bia_app_config_path))
        #f = open(settings.bia_app_config_path, "r")
        with open(settings.bia_app_config_path, 'r+') as f:
        #_dict = app_settings.dict()
            for line in f:
                key, value = line.rstrip("\n").split("=")
                data[key] = value
                print("Line: [{}]={} ".format(key, data[key]))
        f.close()
        print("API Key ID: {} -  API Key: {}".format(invoice_api_key_id, get_api_key(invoice_api_key_id)))
        data["api_key"] = "\""+get_api_key(invoice_api_key_id)+"\""
        data["api_key_id"] = "\""+invoice_api_key_id+"\""
        print("Invoice Config Data = {}".format(data))

        with open(settings.bia_app_config_path, 'w+') as f:
            for key in data:
                f.write("{}={}\n".format(key, data[key]))
        f.close()
    except Exception as e:
        print("Exception occurred during File I/O. {}".format(e))
    return


def set_invoice_adjustment_lambda_settings():
    update_adjustment_env(deploy_settings)
    s3_keyfile = build_s3_keyfile_name(deploy_settings.bia_application_name, deploy_settings.environment)
    print("Invoice Adjustment Lambda S3 Key filename = {}".format(s3_keyfile))
    lambda_app_settings = bia_AppSettings(_env_file=deploy_settings.bia_app_config_path, _env_file_encoding="utf-8")
    # lambda_app_settings.api_key_id = invoice_api_key_id
    # lambda_app_settings = set_api_key(lambda_app_settings)
    serialize_to_s3(lambda_app_settings, deploy_settings.s3_bucket, deploy_settings.bia_application_name, deploy_settings.environment)
    return


def set_ns_notifier_lambda_settings():
    s3_keyfile = build_s3_keyfile_name(deploy_settings.nsnotify_application_name, deploy_settings.environment)
    print("NetSuite Notifier Lambda S3 Key filename = {}".format(s3_keyfile))
    lambda_app_settings = nsnotifier_AppSettings(_env_file=deploy_settings.nsnotify_app_config_path, _env_file_encoding="utf-8")
    serialize_to_s3(lambda_app_settings, deploy_settings.s3_bucket, deploy_settings.nsnotify_application_name, deploy_settings.environment)
    return




with open('outputs.json') as json_file:
    data = json.load(json_file)
json_file.close()

print("CDK Outputs: {}".format(data))
for key in data[deploy_settings.environment + "-" + deploy_settings.application_name]:
    print("KEY {} = Value: {}".format(key, data[deploy_settings.environment + "-" + deploy_settings.application_name][key]))
    if is_invoice_api_key_id(key):
        invoice_api_key_id = data[deploy_settings.environment + "-" + deploy_settings.application_name][key]
    is_dbhostname(key)
    if is_dbSecretName(key):
        secrets = get_secrets(data[deploy_settings.environment + "-" + deploy_settings.application_name][key])
        update_docdb_settings()
        print("Secret Values: {}".format(secrets))

update_api_app_settings()

set_invoice_adjustment_lambda_settings()

set_ns_notifier_lambda_settings()
