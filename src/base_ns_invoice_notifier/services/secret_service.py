import json
import boto3
from botocore.exceptions import ClientError
from config import app_constants as constants
from exceptions.exceptions import SecretsManagerConfigurationException


class SecretsManagerService:
    region = constants.EMPTY
    app_secret_name = constants.EMPTY
    db_username = constants.EMPTY
    db_password = constants.EMPTY

    def __init__(self, secret_name, region):
        self.__configure__(secret_name, region)
        return

    def __configure__(self, secret_name, region):
        self.region = region
        self.app_secret_name = secret_name
        self.__configure_app_secrets__(secret_name)
        self.__validate__()
        return

    def __validate__(self):
        if self.region == constants.EMPTY:
            sme = SecretsManagerConfigurationException()
            sme.message = "SecretsManagerService error. No region defined!"
            raise sme
        elif self.app_secret_name == constants.EMPTY:
            e = SecretsManagerConfigurationException()
            e.message = "SecretsManagerService error. SecretName is Empty!"
            raise e
        return

    def __get_secrets__(self, secret_name):
        """
        This method querys AWS SecretsManager and returns a dictionary containing Key Value pairs for
        the requested Secret Name parameter
        Parameters
        ----------
        secret_name  the name of the Secret

        Returns
        -------
        Dictionary of Key Value pairs

        """
        secrets_dict = {}
        print("Getting Secrets: Region: {} - Secret: {}".format(self.region, secret_name))
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region,
        )

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
                secrets_dict = json.loads(secret_value)
                # print("Secrets dict: {} \n".format(str(dict)))
            else:
                secret_value = secret_response['SecretBinary']
                secrets_dict = json.loads(secret_value)
                # print("Secret Binary  dict: {}".format(str(dict)))
        return secrets_dict

    def __configure_app_secrets__(self, secret_name):
        """
        This method gets Tempus RNID and RNSECRET values stored in AWS Secrets Manager
        and saves them to the servcie instance.

        Parameters
        ----------
        secret_name   the name of the Secret in AWS

        Returns
        -------
        NONE

        """
        secrets_dict = self.__get_secrets__(secret_name)
        for key in secrets_dict:
            setattr(self, key, secrets_dict[key])
        return

    def get_dict(self):
        """
        Returns dictionary of API Keys managed by this service.

        Returns
        -------
        Dictionary of SecretsManagerService attributes

        """
        return self.__dict__

    def get_username(self):
        """
        Returns an database username.

        Parameters
        ----------
        None

        Returns
        -------
        The username String

        """
        return self.db_username

    def get_password(self):
        """
        Returns the database password.

        Parameters
        ----------
        None

        Returns
        -------
        The password String

        """
        return self.db_password

    def get_secret(self, secret_name, region):
        # secret_name = "MySecretName"
        # region_name = "us-west-2"
        credentials = {}
        print("Getting Secrets: Region: {} - Secret: {}".format(region, secret_name))
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region,
        )

        try:
            print("Calling client.get_secret_value({})".format(secret_name))
            secret_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                msg = "The requested secret " + secret_name + " was not found"
                print(msg)
                e2 = Exception(msg)
                raise e2
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                msg = "The request was invalid due to: {}".format(e)
                print(msg)
                e2 = Exception(msg)
                raise e2
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                msg = "The request had invalid parameters: ".format(e)
                print(msg)
                e2 = Exception(msg)
                raise e2
        else:
            # Secrets Manager decrypts the secret value using the associated KMS CMK
            # Depending on whether the secret was a string or binary, only one of these fields will be populated
            if 'SecretString' in secret_response:
                secret_value = secret_response['SecretString']
                credentials = json.loads(secret_value)
            else:
                secret_value = secret_response['SecretBinary']
                credentials = json.loads(secret_value)
        return credentials
