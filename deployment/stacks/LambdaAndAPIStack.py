from typing import Mapping
import os, sys, subprocess
from pydantic_kms_secrets import decrypt_kms_secrets
from aws_cdk import (
    aws_lambda as _lambda,
    aws_dynamodb as ddb,
    aws_apigateway as apigw,
    core,
    aws_ssm as ssm,
    aws_iam as _iam,
    aws_sqs as _sqs,
    aws_sns as _sns,
    aws_sns_subscriptions as _subscriptions,
    aws_certificatemanager as _cert,
    aws_route53 as _route53,
    aws_route53_targets as _targets
)
#update syspath so it can find the appsettings file
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
parentparent = os.path.dirname(parentdir)
sys.path.append(parentparent)
import src.api.config.AppSettings as _appsettings


class LambdaAndAPIStack(core.Stack):
    app_settings:_appsettings = None
    base_name:str  = None
    environment_name: str = None #ex: qa, dev, dev_1
    application_name: str = None
    name_spacer: str = None
    resource_name_singular: str = None
    resource_name_plural: str = None
    def __init__(self, scope: core.Construct, construct_id: str, **deploykwargs) -> None:
        super().__init__(scope, construct_id)
        # get configuration
        self.app_config_file_path = deploykwargs.get('app_config_path')
        self.app_settings = _appsettings.AppSettings(_env_file=self.app_config_file_path, _env_file_encoding='utf-8')
        # set local variable values to be used in the deploy
        self.application_name=deploykwargs.get('application_name')
        print(deploykwargs)
        print(deploykwargs.get('application_name'))
        print('app'+str(self.application_name))
        self.environment_name = deploykwargs.get("environment")
        print('env'+str(self.environment_name))
        self.name_spacer = deploykwargs.get('aws_resource_name_spacer')
        self.resource_name_singular = deploykwargs.get('resource_name_singular')
        self.resource_name_plural = deploykwargs.get('resource_name_plural')
        # The base name will be used to name all constructs and resources.  if there are changes to the standard they will be implemented in one place
        self.base_name = self.getBaseName(**deploykwargs)
        #create table
        application_table = self.createTable(**deploykwargs)
        #create topic, queues and subscription for api events
        notification_topic = self.createAPINotificationTopicAndSubscriptionQueue()
        #create lambda and api gateway
        api = self.createLambdaAndAPIGateway(table_construct=application_table, notification_topic_construct=notification_topic, **deploykwargs)
        #create hosted zone, api gateway domain name and application routes
        self.createHostedZoneAndAPIRoutes(api,**deploykwargs)
        return
    def getBaseName(self, **deploykwargs):
        _baseName = self.environment_name + self.name_spacer+self.application_name
        #no spaces allowed
        _baseName = _baseName.replace(' ','')
        return _baseName
    def createTable(self, **deploykwargs):
        #this solution is based on a single table being required.  if more are required, some refactoring will be needed
        #basically the tablename will be the base stack name+resourcename ex: dev-ref-data-services-revenue-type-map
        table_name = self.base_name+self.name_spacer+self.resource_name_singular
        construct_name = table_name
        retaintable = deploykwargs.get('retain_table_on_stack_destroy')
        retentionPolicy:core.RemovalPolicy
        if(retaintable):
            retentionPolicy = core.RemovalPolicy.RETAIN
        else:
            retentionPolicy = core.RemovalPolicy.DESTROY
        table_construct = ddb.Table(self, construct_name, table_name=table_name,
                                    partition_key={'name': 'id', 'type': ddb.AttributeType.STRING},
                                    removal_policy=retentionPolicy
        )
        return table_construct
    def makeNameUrlFriendly(self, name:str):
        urlFriendlyName = name.replace(' ','-').replace('_','-').lower()
        return urlFriendlyName
    def createLambdaAndAPIGateway(self, table_construct, notification_topic_construct, **deploykwargs):
        logging_queue_arn = deploykwargs.get('logging_queue_arn')  # common to all applications
        lambda_name = self.base_name+self.name_spacer+'api_lambda'
        lambda_construct_name = lambda_name
        api_name = self.base_name+self.name_spacer+"api"
        api_construct_name = api_name
        usage_plan_name = self.base_name + self.name_spacer+"usage-plan"
        api_key_name = self.base_name + self.name_spacer+"api-key"
        deployed_lambda = _lambda.Function(
            self,
            lambda_construct_name,
            runtime=_lambda.Runtime.PYTHON_3_8,
            function_name=lambda_name,
            code=_lambda.Code.asset(f'../src'),
            handler='reference_data_api.api_app.handler',
            environment={
                **(self.app_settings.get_dict())
            },
            layers=[
                self.create_dependencies_layer(self.base_name, lambda_construct_name)
            ]
        )
        lambdaPolicyStatement = _iam.PolicyStatement(effect=_iam.Effect.ALLOW,
                                                     actions=['lambda:InvokeFunction',
                                                              "dynamodb:BatchGet*",
                                                              "dynamodb:DescribeStream",
                                                              "dynamodb:DescribeTable",
                                                              "dynamodb:Get*",
                                                              "dynamodb:Query",
                                                              "dynamodb:Scan",
                                                              "dynamodb:BatchWrite*",
                                                              "dynamodb:CreateTable",
                                                              "dynamodb:Delete*",
                                                              "dynamodb:Update*",
                                                              "dynamodb:PutItem",
                                                              "sqs:Get*",
                                                              "sqs:List*",
                                                              "sqs:SendMessage",
                                                              "sqs:SendMessageBatch",
                                                              "sqs:ReceiveMessage",
                                                              "sqs:CreateQueue",
                                                              "sqs:PurgeQueue",
                                                              "sqs:DeleteMessage",
                                                              "sqs:DeleteMessageBatch",
                                                              "SNS:Publish"
                                                              ],
                                                     resources=[table_construct.table_arn,
                                                                notification_topic_construct.topic_arn,
                                                                logging_queue_arn])

        deployed_lambda.add_to_role_policy(lambdaPolicyStatement)
        #in the api's config, there should be a matching setting with these names.  if more than one table is required then changes must be made
        ## this implementation is based on a single table app
        deployed_lambda.add_environment("table_name", table_construct.table_name)
        deployed_lambda.add_environment("sns_endpoint", notification_topic_construct.topic_arn)
        apiDeployOptions = apigw.StageOptions(
            logging_level=apigw.MethodLoggingLevel.INFO,
            metrics_enabled=True,
            throttling_burst_limit=100,
            throttling_rate_limit=5,
            stage_name=self.environment_name,
            tracing_enabled=False)

        api = apigw.LambdaRestApi(self, api_construct_name,
                                  api_key_source_type=apigw.ApiKeySourceType.HEADER,
                                  handler=deployed_lambda,
                                  rest_api_name=api_name,
                                  default_method_options=apigw.MethodOptions(api_key_required=True),
                                  deploy_options=apiDeployOptions,
                                  endpoint_types=[apigw.EndpointType.REGIONAL],
                                  )
        api.add_usage_plan(
            id=usage_plan_name,
            api_key=api.add_api_key(id=api_key_name, api_key_name=api_key_name),
            api_stages=[apigw.UsagePlanPerApiStage(api=api, stage=api.deployment_stage)],
            description=usage_plan_name,
            name=usage_plan_name
        )

        return api
    def createAPINotificationTopicAndSubscriptionQueue(self):
        #by default only one resource is required and only one queue and topic should be required.  when more are required customizations will be needed here
        notification_construct_name=self.environment_name + self.name_spacer + self.application_name + self.name_spacer +self.resource_name_singular+'_Events_Topic'
        topic_name = notification_construct_name
        sqs_construct_name = self.environment_name + self.name_spacer+self.resource_name_singular+self.name_spacer+"queue"
        sqs_name = sqs_construct_name
        dlq_construct_name = self.environment_name + self.name_spacer + self.resource_name_singular+self.name_spacer+"dlq"
        dlq_name = dlq_construct_name
        notification_topic = _sns.Topic(self,notification_construct_name,display_name=topic_name, topic_name=topic_name)
        rev_type_event_DLQ = _sqs.Queue(self, dlq_construct_name, queue_name=dlq_name)
        rev_type_event_queue = _sqs.Queue(self,sqs_construct_name, queue_name=sqs_name,
                                          visibility_timeout=core.Duration.minutes(30),
                                          dead_letter_queue={'queue': rev_type_event_DLQ, 'max_receive_count': 5},
                                          max_message_size_bytes=1024
                                          )
        notification_topic.add_subscription(_subscriptions.SqsSubscription(queue=rev_type_event_queue, raw_message_delivery=True))
        return notification_topic
    def getHostedZone(self, hosted_zone_name: str, hosted_zone_id: str):
        #if the hosted zone exists already the zone will have a non-blank value.  if it does then create a hosted zone
        #construct from the existing zone  else create a new zone
        hostedZone = None
        hosted_zone_construct_name = hosted_zone_name
        if(hosted_zone_id==''):
            #create a new zone
            hostedZone = _route53.HostedZone(self, hosted_zone_construct_name, zone_name=hosted_zone_name)
        else:
            #create a reference to the existing hosted zone
            hostedZone = _route53.HostedZone.from_hosted_zone_attributes(self, hosted_zone_construct_name, hosted_zone_id=hosted_zone_id,zone_name=hosted_zone_name)
        return hostedZone
    def createHostedZoneAndAPIRoutes(self, api_construct, **deploykwargs):
        """
        creates a new zone for the application, application_name.domain, followed by domain name in api gateway for the environment
        env.application_name.domain
        the first time the stack is run or after its deleted, the cert creation must be manually validated
        This is done by creating a cname record in the newly created hosted zone.  Its easiest to do in aws certificate admin where a button
        is provided
        For subsequent executions of the stack, the cert should be added to the configuration file by arn and recreation won't be attempted.
        for the reference implementation dev it would be dev.reference-data-services.base-nf.iheartmedia.com
        create a reference to the existing cert, no new cert required
        """
        certificate = None
        rootdomain = deploykwargs.get('rootdomain') # root domain is expected to be base.iheartmedia.com or base-np.iheartmedia.com
        # create a zone or get reference to existing
        zone_name = self.makeNameUrlFriendly(self.application_name+'.'+rootdomain)
        zone_id = deploykwargs.get("zone_id")
        zone_exists: bool = zone_id==''
        hosted_zone_construct = self.getHostedZone(zone_name, zone_id)
        #create reference to existing cer
        existing_cert_arn = deploykwargs.get('cert_arn')
        cert_domain = self.environment_name + '.' + zone_name
        cert_construct_name = cert_domain + "cert"
        #if cert arn is not provided this means a new one is required
        if (existing_cert_arn == ''):
            certificate = _cert.Certificate(self, cert_construct_name, domain_name=cert_domain, validation_method=_cert.ValidationMethod.DNS)
        else:
            certificate = _cert.Certificate.from_certificate_arn(self, cert_construct_name, certificate_arn=existing_cert_arn)
        print("the target domain of cert must match this domain " + zone_name)
        #create api_gateway domain_name.  note we don't create on per environment as it creates a need for a new cert
        api_gateway_domain_name = cert_domain  # use to create an alias from the zone to the apigateway domain name the cert va
        api_gateway_domain_name_construct_name = api_gateway_domain_name+self.name_spacer+'domain_name'
        api_gateway_domain_name_construct = apigw.DomainName(self, api_gateway_domain_name_construct_name, certificate=certificate, domain_name=api_gateway_domain_name)
        #create alias record if it the zone is new otherwise expect it exists
        zone_ref_id = zone_name + self.name_spacer+"zoneid"
        alias_record_construct_name = zone_name + self.name_spacer+'AliasRecord'
        _route53.ARecord(self, alias_record_construct_name,
                         target=_route53.RecordTarget.from_alias(_targets.ApiGatewayDomain(api_gateway_domain_name_construct)),
                         zone=_route53.HostedZone.from_hosted_zone_attributes(self, zone_ref_id,hosted_zone_id=zone_id, zone_name=zone_name),
                         record_name=api_gateway_domain_name)
        #get reference to the deployed stage
        deployed_stage = apigw.UsagePlanPerApiStage(api=api_construct, stage=api_construct.deployment_stage).stage
        #add a maping for required resources in the domain.  in most cases you have only one resource but if there are more, additional maps are required here
        singular_path=self.resource_name_singular
        print('singular url path '+singular_path)
        plural_path = self.resource_name_plural
        print('plural url path '+plural_path)
        api_gateway_domain_name_construct.add_base_path_mapping(target_api=api_construct, stage=deployed_stage, base_path=singular_path)
        api_gateway_domain_name_construct.add_base_path_mapping(target_api=api_construct, stage=deployed_stage, base_path=plural_path)
        return
    def addStackBasedEnvironmentVariablesToLambda(self, lambda_construct):
        raise Exception("not implemented yet")
        #should receive two dictionaries, one with names of secrets and their values
        # the other with non-secrets names and their values.
        # each is required to exist as optional deploy_settings that can be set.
        # secret_created_in_build = "secrete_created_in_build"
        # encryptedSecret = self.app_settings.encrypt(secret_created_in_build)
        # lambda_construct.add_environment("secrete_created_in_build", encryptedSecret)
        return
    def create_dependencies_layer(self, base_name, function_name: str) -> _lambda.LayerVersion:
        # Here is where we add all the dependencies for the lambda to aws.
        requirements_file = f'../src/requirements.lambda_layer.txt'
        # output_dir = f'../src/.build/{function_name}'
        output_dir = f'../.layersbuild'
        print("puting all dependencies into "+output_dir)
        #if skip_pip is setthen don't do a pip of data into the output folder.
        if not os.environ.get('SKIP_PIP'):
            subprocess.check_call(
                f'pip3 install -r {requirements_file} -t {output_dir}/python'.split()
            )
            #for some reason this thing insists on adding boto stuff, so we delete it via subprocess
            subprocess.check_call(['rm', '-rf',f'{output_dir}/python/boto3'] )
            subprocess.check_call(['rm', '-rf',
                                   f'{output_dir}/python/botocore'])
        layer_id = f'{base_name}-{function_name}-dependencies'
        layer_code = _lambda.Code.from_asset(output_dir)
        return _lambda.LayerVersion(self, layer_id, code=layer_code)
        #************************************************************************
