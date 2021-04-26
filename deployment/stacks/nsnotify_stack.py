import base64
import json
import os
import subprocess
import sys

import boto3
from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as api_gw,
    core,
    aws_iam as _iam, aws_certificatemanager as _cert,
    aws_route53 as _route53,
    aws_route53_targets as _targets,
    aws_sqs as _sqs,
    aws_sns as _sns,
    aws_sns_subscriptions as _subscriptions
)

# update syspath so it can find the appsettings file
from botocore.exceptions import ClientError
from pydantic_kms_secrets import encrypt

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
parentparent = os.path.dirname(parentdir)
sys.path.append(parentparent)
import src.base_ns_invoice_notifier.config.AppSettings as _appsettings


class NSNotifyStack(core.Stack):
    deploy_settings = None

    def __init__(self, scope: core.Construct, id: str, deploy_settings, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # get configuration
        self.deploy_settings = deploy_settings
        self.app_settings = _appsettings.AppSettings(_env_file=self.deploy_settings.nsnotify_app_config_path,
                                                     _env_file_encoding='utf-8')

        # Set local variables to be used during the deployment.
        self.environment_name = self.deploy_settings.environment
        self.name_spacer = self.deploy_settings.aws_resource_name_spacer
        self.base_name = self.getBaseName()
        print('base name for all resources is: ' + self.base_name)

        # 1. Create Queue, and Subscription
        nsnotify_event_queue = self.createNSNotifyQueue()

        # 2. Lambda Construct - create Lambda function, security policy and roles.
        lambda_construct = self.createLambdaFunctionAndRole(nsnotify_event_queue)
        return

    def getBaseName(self):
        # This function removes white space.
        _baseName = self.deploy_settings.environment + \
                    self.deploy_settings.aws_resource_name_spacer + \
                    self.deploy_settings.nsnotify_application_name
        # No spaces allowed
        _baseName = _baseName.replace(' ', '')
        return _baseName

    def createNSNotifyQueue(self):
        sqs_construct_name = self.environment_name + self.name_spacer + self.deploy_settings.nsnotify_application_name + self.name_spacer + "queue"
        sqs_name = sqs_construct_name
        dlq_construct_name = self.environment_name + self.name_spacer + self.deploy_settings.nsnotify_application_name + self.name_spacer + "dlq"
        dlq_name = dlq_construct_name
        nsnotify_event_DLQ = _sqs.Queue(self, dlq_construct_name, queue_name=dlq_name)
        nsnotify_event_queue = _sqs.Queue(self, sqs_construct_name, queue_name=sqs_name,
                                     visibility_timeout=core.Duration.minutes(30),
                                     dead_letter_queue={'queue': nsnotify_event_DLQ, 'max_receive_count': 5},
                                     max_message_size_bytes=1024
                                     )

        notification_topic = _sns.Topic.from_topic_arn(self,
                                                       id=self.environment_name + self.name_spacer +
                                                       self.deploy_settings.nsnotify_application_name +
                                                       self.name_spacer + "topic",
                                                       topic_arn=self.deploy_settings.sns_endpoint
                                                       )
        #filter_mapping = {"isAdjustment": _sns.SubscriptionFilter(conditions=["False"])}
        #filter_mapping = {"isAdjustment": _sns.SubscriptionFilter.string_filter(blacklist=["True"])}
        #filter_mapping = {"isAdjustment": _sns.SubscriptionFilter.string_filter(blacklist=["True"])}
        filter_mapping = {"isAdjustment": _sns.SubscriptionFilter(conditions=["False"])}
        notification_topic.add_subscription(
            _subscriptions.SqsSubscription(queue=nsnotify_event_queue,
                                           raw_message_delivery=True,
                                           filter_policy=filter_mapping
                                           ))
        return nsnotify_event_queue

    def createLambdaFunctionAndRole(self, nsnotify_event_queue):
        # Deploys Boomi Proxy Lambda Function, creates security policies and roles.

        # Set Lambda Function Name
        lambda_name = self.deploy_settings.environment + \
                      self.deploy_settings.aws_resource_name_spacer + \
                      self.deploy_settings.nsnotify_application_name + "-lambda"

        # Create AWS SQS Policy Statement.
        sqs_logging_policy_statement = _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                                            actions=["sqs:Get*",
                                                                     "sqs:List*",
                                                                     "sqs:SendMessage",
                                                                     "sqs:SendMessageBatch",
                                                                     "sqs:ReceiveMessage",
                                                                     "sqs:CreateQueue",
                                                                     "sqs:PurgeQueue",
                                                                     "sqs:DeleteMessage",
                                                                     "sqs:DeleteMessageBatch"],
                                                            resources=[self.deploy_settings.logging_queue_arn,
                                                                       nsnotify_event_queue.queue_arn])

        # Create lambda function execution role.
        lambda_exec_role = _iam.Role(self, self.deploy_settings.environment + \
                                     self.deploy_settings.aws_resource_name_spacer + \
                                     self.deploy_settings.nsnotify_application_name,
                                     assumed_by=_iam.ServicePrincipal("lambda.amazonaws.com"),
                                     managed_policies=[_iam.ManagedPolicy.from_aws_managed_policy_name(
                                         'service-role/AWSLambdaBasicExecutionRole')],
                                     role_name=self.deploy_settings.environment + \
                                               self.deploy_settings.aws_resource_name_spacer + \
                                               self.deploy_settings.nsnotify_application_name + "-role")

        # Add AWS Managed Secrets Manager policy to Lambda execution role.
        lambda_exec_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name('SecretsManagerReadWrite'))

        # Add AWS SNS policy to role: Boto3 (Botocore) required.
        lambda_exec_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSNSFullAccess'))

        # Add AWS S3 access to read app.env file variables
        lambda_exec_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'))

        # Deploy Lambda Function using CDK Lambda Function Construct and configurations.
        lambda_construct = _lambda.Function(
            self,
            lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_8,
            function_name=lambda_name,
            code=_lambda.Code.asset(f'../src/base_ns_invoice_notifier'),
            handler='ns_notifier.lambda_handler',
            environment={**self.app_settings.dict()},
            role=lambda_exec_role,
            layers=[self.create_dependencies_layer(self.stack_name, lambda_name)],
            timeout=core.Duration.seconds(300)
        )

        # Attach SQS custom policy to Lambda function execution role.
        lambda_construct.add_to_role_policy(sqs_logging_policy_statement)

        lambda_construct.add_event_source_mapping(id=self.environment_name + self.name_spacer +
                                                  self.deploy_settings.nsnotify_application_name +
                                                  self.name_spacer + "trigger",
                                                  event_source_arn=nsnotify_event_queue.queue_arn)

        return lambda_construct

    def create_dependencies_layer(self, base_name, function_name: str) -> _lambda.LayerVersion:
        # Here is where we add all the dependencies for the lambdas to aws.
        requirements_file = f'../src/requirements.lambda_layer.txt'
        # output_dir = f'../src/.build/{function_name}'
        output_dir = f'../.layersbuild'
        print("puting all dependencies into " + output_dir)
        # if skip_pip is setthen don't do a pip of data into the output folder.
        if not os.environ.get('SKIP_PIP'):
            subprocess.check_call(
                f'pip3 install -r {requirements_file} -t {output_dir}/python'.split()
            )
            # for some reason this thing insists on adding boto stuff, so we delete it via subprocess
            subprocess.check_call(['rm', '-rf', f'{output_dir}/python/boto3'])
            subprocess.check_call(['rm', '-rf',
                                   f'{output_dir}/python/botocore'])
        layer_id = f'{base_name}-{function_name}-dependencies'
        layer_code = _lambda.Code.from_asset(output_dir)
        return _lambda.LayerVersion(self, layer_id, code=layer_code)