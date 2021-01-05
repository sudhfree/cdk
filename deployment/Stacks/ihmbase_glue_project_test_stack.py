from aws_cdk import (
    aws_iam as iam,
    aws_glue as glue,
    aws_ec2 as ec2,
    aws_redshift as redshift,
    core
)
from datetime import date

today = date.today()

class IhmbaseGlueProjectTestStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        statement = iam.PolicyStatement(
        	
        	actions=["glue:*",
        		"glue:CreateDatabase",
        		"cloudformation:*" ,
                "s3:GetBucketLocation",
                "s3:*",
                "s3:CreateBucket",
                "s3:ListBucket",
                "s3:ListAllMyBuckets",
                "s3:GetBucketAcl",
                "ec2:DescribeVpcEndpoints",
                "ec2:DescribeRouteTables",
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcAttribute",
                "iam:ListRolePolicies",
                "iam:GetRole",
                "iam:GetRolePolicy",
                "cloudwatch:PutMetricData"],
            resources=["*"],
            )
        statemen2 = iam.PolicyStatement(
        	
        	actions=["s3:CreateBucket"],
            resources=["arn:aws:s3:::aws-glue-*"],
            )

        statemen3 = iam.PolicyStatement(
        	
        	actions=["s3:GetObject",
                	"s3:PutObject",
                	"s3:DeleteObject"],
            resources=["arn:aws:s3:::aws-glue-*/*",
                "arn:aws:s3:::*/*aws-glue-*/*",
                "arn:aws:s3:::yourbucket*",
                "arn:aws:s3:::yourbucket*"],
            )

        statemen4 = iam.PolicyStatement(
        	
        	actions=["s3:GetObject"],
            resources=["arn:aws:s3:::crawler-public*",
                "arn:aws:s3:::aws-glue-*"],
            )

        statemen5 = iam.PolicyStatement(
        	
        	actions=[ "logs:CreateLogGroup",
                		"logs:CreateLogStream",
                		"logs:PutLogEvents"],
            resources=["arn:aws:logs:*:*:/aws-glue/*"],
            )

        statemen6 = iam.PolicyStatement(
        	
        	actions=[ "logs:CreateLogGroup",
                		"logs:CreateLogStream",
                		"logs:PutLogEvents"],
            resources=["arn:aws:logs:*:*:/aws-glue/*"],
            )

        Glue_policy = iam.PolicyDocument(statements=[statement,statemen2,statemen3,statemen4,statemen5])

        statementredshift = iam.PolicyStatement(
        	
        	actions=["ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeAddresses",
                "ec2:AssociateAddress",
                "ec2:DisassociateAddress",
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:ModifyNetworkInterfaceAttribute",
                "ec2:CreateVpcEndpoint",
                "ec2:DeleteVpcEndpoints",
                "ec2:DescribeVpcEndpoints",
                "ec2:ModifyVpcEndpoint"],
            resources=["*"],
            )
        redshift_policy = iam.PolicyDocument(statements=[statementredshift])

        redshift_Role = iam.Role(
            self,
            "RedshiftAPIRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            inline_policies = [redshift_policy]
            #managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole ")]
        )

        Glue_Role = iam.Role(
            self,
            "RestAPIRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            inline_policies = [Glue_policy]
            #managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole ")]
        )

        
        '''vpc = ec2.Vpc(
        	self, "TheVPC",
    		cidr="10.192.0.0/16"
		)'''

        glue_database = glue.Database(
            self, 'Glue-database-id',
            database_name = "glue_database_cdk"
        )
        glue_database1 = glue.Database(
            self, 'Glue-database-id1',
            database_name = "glue_database_cdk1"
        )

        '''glue_security = ec2.CfnSecurityGroup(
            self, 'SecurityGroup',
            group_description = "test new",
            group_name = "sgone",
            vpc_id = vpc.vpc_id
        )

        glue_security_two = ec2.CfnSecurityGroup(
            self, 'SecurityGrouptwo',
            group_description = "test new two",
            group_name = "sgtwo",
            vpc_id = vpc.vpc_id
        )

        

        redshift_subnet = ec2.PrivateSubnet(
            self, 'redshidftsubnet',
            availability_zone = "us-east-1",
            cidr_block = "10.0.1.0/24",
            vpc_id = vpc.vpc_id,
        )
        glue_connection = glue.CfnConnection(
            self, 'Connectionnew',
            catalog_id = "778359441486",
            connection_input = {"connectionType":"JDBC","name":"JDBCConnection","physicalConnectionRequirements":{"availabilityZone":"us-east-1","securityGroupIdList":[glue_security.group_name,glue_security_two.group_name]},"connectionProperties":{"JDBC_CONNECTION_URL":"jdbc:redshift://ihmbase-glue-project-test-glueredshiftcluster-1ocwqdlqvvjnf.ckjx2vxh3r6s.us-east-1.redshift.amazonaws.com:5439/glue_database_cdk","USERNAME":"awsuser","Password":"Test.1esttest"}}
        )'''
       

        glue_job = glue.CfnJob(
            self, 'etl_track_ownership',
            command = {"name": "etl_track_ownership","scriptLocation": "s3://aws-glue-scripts-778359441486-us-east-1/admin"},
            role = Glue_Role.role_arn,
            allocated_capacity = 10,
            #connections = {"connections":[glue_connection.catalog_id]},
            execution_property = {"maxConcurrentRuns" : 2},
            #max_capacity = 10,
            max_retries = 2,
            name = 'etl_track_ownership',
            notification_property = {"notifyDelayAfter" : 1},
            #number_of_workers = 1,
            timeout = 10,
            #worker_type = "Standard"
        )

        glue_crawler = glue.CfnCrawler(
            self, 'glue-crawler-id',
            description="Glue Crawler",
            name='Glue Crawler CDK',
            database_name=glue_database.database_name,
            schedule=None,
            role=Glue_Role.role_arn,
            targets={"s3Targets": [{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_artist/data"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_artist"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_catalog_4corp_royalty"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_host_config"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_live_stations_genres_v2"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_live_stations_v2"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_od_subscription"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_profile"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/dim_track"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/fct_custom_radio"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/fct_live_radio"},
            		{"path": "s3://test.in.royal.base.ihm/ihr_dwh/fct_spins_master"}]},

        )


        glue_JDBCcrawler = glue.CfnCrawler(
            self, 'glue-crawlerJDBC-id',
            description="Glue Crawler JDBC",
            name='Glue Crawler JDBC CDK',
            database_name=glue_database1.database_name,
            schedule=None,
            role=Glue_Role.role_arn,
           	targets={"jdbcTargets": [{"connectionName": "glue_connection"}]},

        )
        env = self.node.try_get_context("env")
        glue_workflow = glue.CfnWorkflow(
            self, 'GlueworkFlow',
            tags = {"environment":env,"created_by":"Vishnu Polu","created_on":str(today),"Name":"ihmbase_Royalties2.0","Solution":"Royalties2.0","Disposition":"active"}
        )



        glue_redshift = redshift.CfnCluster(
            self, 'Glueredshiftcluster',
            cluster_type = "single-node",
            db_name = glue_database.database_name,
            master_username = "awsuser",
            master_user_password = "Test.1esttest",
            node_type = "dc2.large",
            iam_roles = [redshift_Role.role_arn],
            vpc_security_group_ids = ["sg-e08563a8"],
            cluster_subnet_group_name = "royalty-redshift-sg",
            port = 5439,
        )

       


        # The code that defines your stack goes here
