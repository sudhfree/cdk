import json
import boto3
from botocore.exceptions import ClientError
from api.config import app_constants as constants
from api.exceptions.SecretsManagerConfigurationException import SecretsManagerConfigurationException


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
        # # TODO: get Secret for Application
        self.__configure_app_secrets__(secret_name)
        # # TODO: get Secret for API Keys
        # self.__configure_api_keys_secrets__(api_key_secret)
        # self.read_secret_config(bucket, secret_file, env, region)
        # TODO: validate this service.
        self.__validate__()
        return

    # def read_secret_config(self, bucket, secret_file, region):
    #     secret_files = self.__get_secret_files__(bucket, secret_file, region)
    #     for file in secret_files:
    #             config = self.__get_secrets__(file)
    #     return

    def __validate__(self):
        if self.db_username == constants.EMPTY:
            sme = SecretsManagerConfigurationException()
            sme.message = "SecretsManagerService error. No Database username defined!"
            raise sme
        elif self.db_password == constants.EMPTY:
            e = SecretsManagerConfigurationException()
            e.message = "SecretsManagerService error. Db Password is Empty!"
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
        dict = {}
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
                dict = json.loads(secret_value)
                # print("Secrets dict: {} \n".format(str(dict)))
            else:
                secret_value = secret_response['SecretBinary']
                dict = json.loads(secret_value)
                # print("Secret Binary  dict: {}".format(str(dict)))
                # self.tempus_rnid = dict["tempus_rnid"]
                # self.tempus_rncert = dict["tempus_rnsecret"]
        return dict

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
        dict = {}
        dict = self.__get_secrets__(secret_name)
        # print("{} Secrets = {}".format(secret_name, dict))
        self.db_username = dict["username"]
        self.db_password = dict["password"]
        return

    def __configure_api_keys_secrets__(self, api_key_secret):
        """
        This method gets API Keys stored in AWS Secrets Manager
        and saves them to the service instance. The API Keys are used
        to determine the MID to be used for Tempus payment processing.

        Parameters
        ----------
        api_key_secret   the name of the AWS secret

        Returns
        -------
        Nones

        """
        self.api_keys = self.__get_secrets__(api_key_secret)
        return

    def get_rnid(self):
        """
        This method gets the value of the Tempus RNID required for
        Tempus API Transaction Requests.

        Returns
        -------
        The value of the current Tempus RNID

        """
        return self.tempus_rnid

    def get_rncert(self):
        """
        This method gets the value of the Tempus RNSECRET required for
        Tempus API Transaction Requests.

        Returns
        -------
        The value of the current Tempus RNSECRET

        """
        return self.tempus_rncert

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

