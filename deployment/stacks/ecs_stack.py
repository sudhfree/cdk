import os, sys
from dotenv import load_dotenv

from aws_cdk.aws_ecr_assets import DockerImageAsset
import os.path
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_elasticloadbalancingv2 as elbv2,
    aws_apigateway as api_gw,
    aws_route53 as _route53,
    aws_certificatemanager as _cert,
    aws_route53_targets as _targets,
    aws_docdb as docdb,
    aws_sns as _sns
    #aws_secretsmanager as secretsmgr
)

class ECSStack(core.Stack):
    deploy_settings = None
    docdb_cluster: docdb.DatabaseCluster = None

    def __init__(self, scope: core.Construct, id: str, deploy_settings, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.deploy_settings = deploy_settings
        # 1. Defines the VPC and subnets
        vpc = self.createVPC()
        vpc_subnets = self.createSubnetsForVPC(vpc)
        # Create DocDB Cluster
        docdb_cluster = self.createDocDBCluster(vpc, vpc_subnets)
        self.docdb_cluster = docdb_cluster
        print("DocDB Host: {}".format(self.docdb_cluster.cluster_endpoint.hostname))
        print("DocDb Secret {}".format(self.docdb_cluster.secret.secret_name))
        print("DocDb Secret Values {}".format(self.docdb_cluster.secret.secret_value.to_json()))
        # 2. Create image and put in repository
        image_repo_asset = self.createImageAndPushToRepo()
        # 3. Creation of Execution Role for our task
        ecs_task_role = self.createECSTaskRole()
        # 4. Creates Elastic Container Service Fargate Cluster
        fargate_cluster = self.createFargateCluster(vpc)
        container_image = self.createContainerFromImage(image_repo_asset)
        # 5. Create a Task Definition for our cluster to invoke a task
        task_definition = self.createFargateTaskDefinition(ecs_task_role)
        # 6. Create container for the task definition from ECR image
        container_definition = self.createContainerDefinition(task_definition, container_image)
        # 7. Add port mappings to your container, Make sure to use TCP protocol for Network Load Balancer (NLB)
        port_mapping = self.createPortMapping(container_definition)
        # 8. Create your own Security Group with Ingress Rules
        serviceSG = self.createSecurityGroupWithIngressRules(vpc)
        # 9. Create Fargate Service
        ecs_service = self.createECSFargateService(fargate_cluster, task_definition, serviceSG)
        # 10. Create the Network Load Balancer using the above VPC
        nlb = self.createNetworkLoadBalancer(vpc, vpc_subnets, ecs_service)
        # 11. Create VPC Link
        vpc_link = self.createVPCLink(nlb)
        # 12. Create API Gateway - resources/methods
        api = self.createAPIGateway(vpc_link, nlb)
        # 13. Create SNS Topic
        notification_topic = self.createTopic()

        self.createHostedZoneAndAPIRoutes(api, self.deploy_settings.rootdomain)
        return

    def getBaseName(self):
        _baseName = self.deploy_settings.environment + \
                    self.deploy_settings.aws_resource_name_spacer + \
                    self.deploy_settings.application_name
        # no spaces allowed
        _baseName = _baseName.replace(' ', '')
        return _baseName

    def create_security_group(self, _vpc, constructName):
        security_group = ec2.SecurityGroup(self, constructName, security_group_name=self.getBaseName() + "-sg",
                                           vpc=_vpc)
        return security_group

    def createVPC(self):
        vpc = ec2.Vpc.from_lookup(self, self.deploy_settings.vpc_id + "-vpc", vpc_id=self.deploy_settings.vpc_id)
        return vpc

    def createSubnetsForVPC(self, vpc):
        sub1 = ec2.Subnet.from_subnet_id(self, "privateSubNet1", subnet_id=self.deploy_settings.privateSubNet1)
        sub2 = ec2.Subnet.from_subnet_id(self, "privateSubNet2", subnet_id=self.deploy_settings.privateSubNet2)
        sub3 = ec2.Subnet.from_subnet_id(self, "privateSubNet3", subnet_id=self.deploy_settings.privateSubNet3)
        sub4 = ec2.Subnet.from_subnet_id(self, "privateSubNet4", subnet_id=self.deploy_settings.privateSubNet4)

        vpc_subnets = ec2.SubnetSelection(subnets=[sub1, sub2, sub3, sub4])
        return vpc_subnets

    def create_docdb_cluster_security_group(self, dbcluster_name, _vpc):
        """
        Creates SecurityGroup for Notification Lambda
        :param dbcluster_name:
        :param _vpc:
        :return: new Security Group
        """
        security_group = ec2.SecurityGroup(self, "docdbClusterSG", security_group_name=dbcluster_name + "-sg", vpc=_vpc)
        security_group.add_ingress_rule(ec2.Peer.ipv4("10.0.0.0/8"), ec2.Port.tcp(27017), "DocDb from VPC")
        return security_group

    def createDocDBCluster(self, vpc, vpc_subnets):
        db_cluster_name = self.deploy_settings.environment + self.deploy_settings.aws_resource_name_spacer + self.deploy_settings.application_name + "-docdb"
        security_group = self.create_docdb_cluster_security_group(db_cluster_name, vpc)
        docdb_instance_props = docdb.InstanceProps(instance_type=ec2.InstanceType(instance_type_identifier=self.deploy_settings.db_instance_type),
                                                   vpc=vpc,
                                                   vpc_subnets=vpc_subnets,
                                                   security_group=security_group
                                                   )

        docdb_parameter_group = docdb.ClusterParameterGroup(self,
                                                            self.deploy_settings.environment +
                                                            self.deploy_settings.aws_resource_name_spacer +
                                                            self.deploy_settings.application_name + '-pg',
                                                            family='docdb3.6',
                                                            parameters={"audit_logs": "disabled",
                                                                        "change_stream_log_retention_duration": "10800",
                                                                        "profiler": "disabled",
                                                                        "profiler_sampling_rate": "1.0",
                                                                        "profiler_threshold_ms": "100",
                                                                        "tls": "disabled",
                                                                        "ttl_monitor": "disabled"},
                                                            db_cluster_parameter_group_name=self.deploy_settings.environment +
                                                            self.deploy_settings.aws_resource_name_spacer +
                                                            self.deploy_settings.application_name + '-pg',
                                                            description=self.deploy_settings.environment +
                                                            self.deploy_settings.aws_resource_name_spacer +
                                                            self.deploy_settings.application_name + " document db parameter group"
                                                            )

        docdb_cluster = docdb.DatabaseCluster(self, "Database",
                                              instance_props=docdb_instance_props,
                                              master_user=docdb.Login(username=self.deploy_settings.dbUser, ),
                                              db_cluster_name=self.deploy_settings.environment +
                                              self.deploy_settings.aws_resource_name_spacer +
                                              self.deploy_settings.application_name + "-docdb",
                                              instances=self.deploy_settings.db_instance_count,
                                              parameter_group=docdb_parameter_group
                                              )

        core.CfnOutput(docdb_cluster, db_cluster_name + "-hostname",
                       value=docdb_cluster.cluster_endpoint.hostname,
                       export_name=self.deploy_settings.environment +
                                   self.deploy_settings.application_name +
                                   "-Invoice-API-DocDbHost")

        core.CfnOutput(docdb_cluster, db_cluster_name + "-secret",
                       value=docdb_cluster.secret.secret_name,
                       export_name=self.deploy_settings.environment +
                                   self.deploy_settings.application_name +
                                   "-Invoice-API-DocDbSecretName")

        return docdb_cluster

    def createImageAndPushToRepo(self):
        image_repo_asset = DockerImageAsset(self, self.deploy_settings.environment +
                                            self.deploy_settings.aws_resource_name_spacer +
                                            self.deploy_settings.application_name + '-image',
                                            directory="../src",  # os.path.join(dirname, 'dev-fg-ddb-ref-data-svcs'),
                                            repository_name=self.deploy_settings.environment +
                                            self.deploy_settings.aws_resource_name_spacer +
                                            self.deploy_settings.application_name)
        return image_repo_asset

    def createECSTaskRole(self):
        """
        create ecs task role that will be assigned to fargate task instances
        :return: role
        """
        ecs_task_role = iam.Role(self,
                                 self.deploy_settings.environment +
                                 self.deploy_settings.aws_resource_name_spacer +
                                 self.deploy_settings.application_name + "-taskExecutionRole",
                                 assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
                                 managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonECSTaskExecutionRolePolicy')],
                                 role_name=self.deploy_settings.environment +
                                 self.deploy_settings.aws_resource_name_spacer +
                                 self.deploy_settings.application_name + "-taskExecutionRole")
        ecs_task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSQSFullAccess'))
        ecs_task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDocDBFullAccess'))
        ecs_task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSNSFullAccess'))
        ecs_task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'))
        return ecs_task_role

    def createFargateCluster(self, vpc):
        fargate_cluster = ecs.Cluster(self,
                                      id=self.deploy_settings.environment +
                                      self.deploy_settings.aws_resource_name_spacer +
                                      self.deploy_settings.application_name + "-cluster",
                                      cluster_name=self.deploy_settings.environment +
                                      self.deploy_settings.aws_resource_name_spacer +
                                      self.deploy_settings.application_name,
                                      vpc=vpc)
        return fargate_cluster

    def createContainerFromImage(self, image_repo_asset):
        container_image = ecs.ContainerImage.from_docker_image_asset(image_repo_asset)
        return container_image

    def createFargateTaskDefinition(self, ecs_task_role):
        task_definition = ecs.FargateTaskDefinition(
            scope=self,
            id=self.deploy_settings.environment +
            self.deploy_settings.aws_resource_name_spacer +
            self.deploy_settings.application_name + "-td",
            family=self.deploy_settings.environment +
            self.deploy_settings.aws_resource_name_spacer +
            self.deploy_settings.application_name + "-td",
            execution_role=ecs_task_role,
            task_role=ecs_task_role,
            memory_limit_mib=self.deploy_settings.task_definition_memory_limit_mib,
            cpu=self.deploy_settings.task_definition_cpu
        )
        return task_definition

    def createContainerDefinition(self, task_definition, container_image):
        container_definition = task_definition.add_container(
            id=self.deploy_settings.environment +
               self.deploy_settings.aws_resource_name_spacer +
               self.deploy_settings.application_name + "-ctr",
            image=container_image,
            logging=ecs.AwsLogDriver(
                stream_prefix=self.deploy_settings.environment +
                              self.deploy_settings.aws_resource_name_spacer +
                              self.deploy_settings.application_name)
        )
        return container_definition

    def createPortMapping(self, container_definition):
        port_mapping = ecs.PortMapping(container_port=8080, host_port=8080, protocol=ecs.Protocol.TCP)
        container_definition.add_port_mappings(port_mapping)
        return port_mapping

    def createSecurityGroupWithIngressRules(self, vpc):
        serviceSG = self.create_security_group(vpc, self.getBaseName() + "-svc-sg")
        serviceSG.add_ingress_rule(ec2.Peer.ipv4("10.0.0.0/8"), ec2.Port.tcp(8080), "HTTP from VPC")
        serviceSG.add_ingress_rule(ec2.Peer.ipv4("10.0.0.0/8"), ec2.Port.tcp(80), "HTTP from VPC")
        return serviceSG

    def createECSFargateService(self, fargate_cluster, task_definition, serviceSG):
        ecs_service = ecs.FargateService(self,
                                         self.deploy_settings.environment +
                                         self.deploy_settings.aws_resource_name_spacer +
                                         self.deploy_settings.application_name + "-svc",
                                         cluster=fargate_cluster,
                                         desired_count=self.deploy_settings.service_desired_count,
                                         task_definition=task_definition,
                                         service_name=self.deploy_settings.environment +
                                         self.deploy_settings.aws_resource_name_spacer +
                                         self.deploy_settings.application_name + "-svc",
                                         security_groups=[serviceSG]
                                         )
        return ecs_service

    def createNetworkLoadBalancer(self, vpc, vpc_subnets, ecs_service):
        # Create the Network Load Balancer using the above VPC
        nlb = elbv2.NetworkLoadBalancer(self,
                                        self.deploy_settings.environment +
                                        self.deploy_settings.aws_resource_name_spacer +
                                        self.deploy_settings.application_name + "-nlb",
                                        vpc=vpc,
                                        internet_facing=False,
                                        load_balancer_name=self.deploy_settings.environment +
                                        self.deploy_settings.aws_resource_name_spacer +
                                        self.deploy_settings.application_name + "-nlb",
                                        vpc_subnets=vpc_subnets
                                        )

        # Add a listener on a particular port for the NLB
        nlb_listener = nlb.add_listener(self.deploy_settings.environment +
                                        self.deploy_settings.aws_resource_name_spacer +
                                        self.deploy_settings.application_name + "-lstnr",
                                        port=80)

        # Add Fargate service to the listener
        nlb_listener.add_targets(self.deploy_settings.environment +
                                 self.deploy_settings.aws_resource_name_spacer +
                                 self.deploy_settings.application_name + "-trgt",
                                 port=80,
                                 target_group_name=self.deploy_settings.environment +
                                                   self.deploy_settings.aws_resource_name_spacer +
                                                   self.deploy_settings.application_name + "-trgt",
                                 targets=[ecs_service]
                                 )
        return nlb

    def createVPCLink(self, nlb):
        vpc_link = api_gw.VpcLink(self,
                                  self.deploy_settings.environment +
                                  self.deploy_settings.aws_resource_name_spacer +
                                  self.deploy_settings.application_name + "-VPCLink", targets=[nlb],
                                  vpc_link_name=self.deploy_settings.environment +
                                                self.deploy_settings.aws_resource_name_spacer +
                                                self.deploy_settings.application_name)
        return vpc_link


    def createAPIGateway(self, vpc_link, nlb):

        usage_plan_name = (self.deploy_settings.environment +
                           self.deploy_settings.aws_resource_name_spacer +
                           self.deploy_settings.application_name + "-usage-plan")

        api_key_name = (self.deploy_settings.environment +
                        self.deploy_settings.aws_resource_name_spacer +
                        self.deploy_settings.application_name + "-key")


        usage_plan_api_key = api_gw.ApiKey(self,
                                           api_key_name,
                                           enabled=True,
                                           api_key_name=api_key_name
                                           )


        api_deploy_options = api_gw.StageOptions(
            logging_level=api_gw.MethodLoggingLevel.INFO,
            metrics_enabled=True,
            throttling_burst_limit=100,
            throttling_rate_limit=5,
            stage_name=self.deploy_settings.environment,
            tracing_enabled=False
        )

        api = api_gw.RestApi(self,
                             self.deploy_settings.environment +
                             self.deploy_settings.aws_resource_name_spacer +
                             self.deploy_settings.application_name + "-api",
                             description=self.deploy_settings.rest_api_description,
                             rest_api_name=self.deploy_settings.environment +
                                           self.deploy_settings.aws_resource_name_spacer +
                                           self.deploy_settings.application_name + "-api",
                             deploy_options=api_deploy_options,
                             endpoint_types=[api_gw.EndpointType.REGIONAL],
                             default_method_options=api_gw.MethodOptions(api_key_required=True)
                             )
        api.add_usage_plan(
            id=usage_plan_name,
            api_key=usage_plan_api_key,
            api_stages=[api_gw.UsagePlanPerApiStage(api=api, stage=api.deployment_stage)],
            description=usage_plan_name,
            name=usage_plan_name
        )


        core.CfnOutput(usage_plan_api_key,
                       self.deploy_settings.environment +
                       self.deploy_settings.aws_resource_name_spacer +
                       self.deploy_settings.application_name + "-usage-plan-api-key",
                       value=usage_plan_api_key.key_id)


        integration_options_POST = api_gw.IntegrationOptions(connection_type=api_gw.ConnectionType.VPC_LINK,
                                                             vpc_link=vpc_link)

        integration_POST = api_gw.Integration(type=api_gw.IntegrationType.HTTP_PROXY,
                                              integration_http_method="POST",
                                              options=integration_options_POST,
                                              uri="http://" + nlb.load_balancer_dns_name + "/" + self.deploy_settings.root_resource_name
                                              )

        revenue_type_map = api.root.add_resource(self.deploy_settings.root_resource_name)
        revenue_type_map.add_method("POST", integration_POST, api_key_required=True)
        integration_options_GET = api_gw.IntegrationOptions(connection_type=api_gw.ConnectionType.VPC_LINK,
                                                            request_parameters={"integration.request.path.revid": "method.request.path.revid"},
                                                            vpc_link=vpc_link
                                                            )
        integration_GET = api_gw.Integration(type=api_gw.IntegrationType.HTTP_PROXY,
                                             integration_http_method="GET",
                                             options=integration_options_GET,
                                             uri="http://" + nlb.load_balancer_dns_name + "/"+self.deploy_settings.root_resource_name+"/{revid}"
                                             )

        integration_options_PUT = api_gw.IntegrationOptions(connection_type=api_gw.ConnectionType.VPC_LINK,
                                                            request_parameters={
                                                             "integration.request.path.revid": "method.request.path.revid"},
                                                            vpc_link=vpc_link
                                                            )

        integration_PUT = api_gw.Integration(type=api_gw.IntegrationType.HTTP_PROXY,
                                             integration_http_method="PUT",
                                             options=integration_options_PUT,
                                             uri="http://" + nlb.load_balancer_dns_name + "/" + self.deploy_settings.root_resource_name + "/{revid}"
                                             )

        integration_options_DELETE = api_gw.IntegrationOptions(connection_type=api_gw.ConnectionType.VPC_LINK,
                                                               request_parameters={
                                                                "integration.request.path.revid": "method.request.path.revid"},
                                                               vpc_link=vpc_link
                                                               )

        integration_DELETE = api_gw.Integration(type=api_gw.IntegrationType.HTTP_PROXY,
                                                integration_http_method="DELETE",
                                                options=integration_options_DELETE,
                                                uri="http://" + nlb.load_balancer_dns_name + "/" + self.deploy_settings.root_resource_name + "/{revid}"
                                                )

        integration_options_PATCH = api_gw.IntegrationOptions(connection_type=api_gw.ConnectionType.VPC_LINK,
                                                              request_parameters={
                                                                   "integration.request.path.revid": "method.request.path.revid"},
                                                              vpc_link=vpc_link
                                                              )

        integration_PATCH = api_gw.Integration(type=api_gw.IntegrationType.HTTP_PROXY,
                                               integration_http_method="PATCH",
                                               options=integration_options_PATCH,
                                               uri="http://" + nlb.load_balancer_dns_name + "/" + self.deploy_settings.root_resource_name + "/{revid}"
                                               )

        rev_id = revenue_type_map.add_resource(path_part="{revid}", default_integration=integration_GET)
        rev_id.add_method("GET", integration_GET, api_key_required=True, request_parameters={"method.request.path.revid": True})
        rev_id.add_method("PUT", integration_PUT, api_key_required=True, request_parameters={"method.request.path.revid": True})
        rev_id.add_method("DELETE", integration_DELETE, api_key_required=True, request_parameters={"method.request.path.revid": True})
        rev_id.add_method("PATCH", integration_PATCH, api_key_required=True, request_parameters={"method.request.path.revid": True})
        return api

    def createTopic(self):
        notification_construct_name = self.deploy_settings.environment + self.deploy_settings.aws_resource_name_spacer + self.deploy_settings.application_name + "-topic"
        topic_name = notification_construct_name
        notification_topic = _sns.Topic(self, notification_construct_name, display_name=topic_name, topic_name=topic_name)
        return notification_topic

    def makeNameUrlFriendly(self, name: str):
        urlFriendlyName = name.replace(' ', '-').replace('_', '-').lower()
        return urlFriendlyName

    def createHostedZoneAndAPIRoutes(self, api_construct, _rootdomain, **deploykwargs):
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
        rootdomain = self.deploy_settings.rootdomain  # root domain is expected to be base.iheartmedia.com or base-np.iheartmedia.com
        application_name_URL_part = self.makeNameUrlFriendly(
            self.deploy_settings.environment + self.deploy_settings.env_to_domain_separator +
            self.deploy_settings.application_name)
        print("Root Domain is: {}".format(rootdomain))
        # create a zone or get reference to existing
        zone_id = self.deploy_settings.zone_id
        hosted_zone_construct = _route53.HostedZone.from_hosted_zone_attributes(self,
                                                                                self.getBaseName() + 'zone',
                                                                                hosted_zone_id=zone_id,
                                                                                zone_name=rootdomain)
        # create reference to existing cer
        existing_cert_arn = self.deploy_settings.cert_arn
        # new
        application_full_domain_name = application_name_URL_part + '.' + rootdomain
        # New
        cert_domain = application_full_domain_name
        cert_construct_name = cert_domain + "cert"
        print('cert domain will be ' + cert_domain)
        # if cert arn is not provided this means a new one is required
        if (existing_cert_arn == ''):
            certificate = _cert.Certificate(self, cert_construct_name, domain_name=cert_domain,
                                            validation_method=_cert.ValidationMethod.DNS)
        else:
            certificate = _cert.Certificate.from_certificate_arn(self, cert_construct_name,
                                                                 certificate_arn=existing_cert_arn)
        print("the target domain of cert must match this domain " + cert_domain)
        # create api_gateway domain_name.  note we don't create on per environment as it creates a need for a new cert
        api_gateway_domain_name = cert_domain  # use to create an alias from the zone to the apigateway domain name the cert va
        api_gateway_domain_name_construct_name = api_gateway_domain_name + self.deploy_settings.aws_resource_name_spacer + 'domain_name'
        api_gateway_domain_name_construct = api_gw.DomainName(self, api_gateway_domain_name_construct_name,
                                                              certificate=certificate,
                                                              domain_name=api_gateway_domain_name)
        # create alias record if it the zone is new otherwise expect it exists
        ##new
        zone_ref_id = application_full_domain_name + self.deploy_settings.aws_resource_name_spacer + "zoneid"
        ##new
        alias_record_construct_name = application_full_domain_name + self.deploy_settings.aws_resource_name_spacer + 'AliasRecord'
        # new
        _route53.ARecord(self, alias_record_construct_name,
                         target=_route53.RecordTarget.from_alias(
                             _targets.ApiGatewayDomain(api_gateway_domain_name_construct)),
                         zone=_route53.HostedZone.from_hosted_zone_attributes(self, zone_ref_id, hosted_zone_id=zone_id,
                                                                              zone_name=rootdomain),
                         record_name=application_name_URL_part)

        # get reference to the deployed stage
        deployed_stage = api_gw.UsagePlanPerApiStage(api=api_construct, stage=api_construct.deployment_stage).stage
        # add a maping for required resources in the domain.  in most cases you have only one resource but if there are more, additional maps are required here
        # singular_path=self.deploy_settings.resource_name_singular
        # print('singular url path '+singular_path)
        # plural_path = self.deploy_settings.resource_name_plural
        # print('plural url path '+plural_path)
        api_gateway_domain_name_construct.add_base_path_mapping(target_api=api_construct, stage=deployed_stage)
        return
