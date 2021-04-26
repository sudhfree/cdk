#!/usr/bin/env python3
import os, sys

from aws_cdk import core
import config.DeploySettings as _deploysettings
from stacks.LambdaAndAPIStack import LambdaAndAPIStack
from fastapi_pagination import Page, pagination_params, PaginationParams, paginate
from pydantic_kms_secrets import decrypt_kms_secrets
from stacks.ecs_stack import ECSStack
from aws_cdk.aws_docdb import DatabaseCluster
from stacks.bia_stack import BIAStack
from stacks.nsnotify_stack import NSNotifyStack


currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

app = core.App()

deploysettings = _deploysettings.DeploySettings(_env_file='deploy.env', _env_file_encoding='utf-8')
aws_env = core.Environment(account=deploysettings.env_account, region=deploysettings.env_region)

stack_instance = ECSStack(app, deploysettings.environment + deploysettings.aws_resource_name_spacer + deploysettings.application_name, deploysettings, env=aws_env)
stack_instance2 = BIAStack(app, deploysettings.environment + deploysettings.aws_resource_name_spacer + deploysettings.bia_application_name, deploysettings, env=aws_env)
stack_instance3 = NSNotifyStack(app, deploysettings.environment + deploysettings.aws_resource_name_spacer + deploysettings.nsnotify_application_name, deploysettings, env=aws_env)

core.Tags.of(stack_instance).add("Solution", deploysettings.environment + deploysettings.aws_resource_name_spacer + deploysettings.application_name)
core.Tags.of(stack_instance).add("Environment", deploysettings.environment)
core.Tags.of(stack_instance).add("Disposition", deploysettings.tag_disposition)
core.Tags.of(stack_instance).add("CreatedDate", deploysettings.tag_created_date)
core.Tags.of(stack_instance).add("CreatedBy", deploysettings.tag_created_by)
core.Tags.of(stack_instance).add("Name", deploysettings.environment + deploysettings.aws_resource_name_spacer + deploysettings.application_name)

app.synth()
cluster = stack_instance.docdb_cluster
print("DocDb cluster resource identifier: {}".format(cluster.cluster_resource_identifier))
print("DocDb cluster identifier: {}".format(cluster.cluster_identifier))
print("DocDB Host: {}".format(cluster.cluster_endpoint.hostname))
print("DocDb Secret {}".format(cluster.secret.secret_name))
print("DocDb Secret Values {}".format(cluster.secret.secret_value.to_json()))
