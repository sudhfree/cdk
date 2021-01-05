#!/usr/bin/env python3

from aws_cdk import core

from Stacks.ihmbase_glue_project_test_stack import IhmbaseGlueProjectTestStack
env_USA = core.Environment(account="778359441486", region="us-east-1")

app = core.App()
ref_implementation_stack = IhmbaseGlueProjectTestStack(app, "ihmbase-glue-project-test", **deploysettings.dict())
core.Tags.of(ref_implementation_stack).add("Name", "royalties-glue")
core.Tags.of(ref_implementation_stack).add("disposition", "active")
core.Tags.of(ref_implementation_stack).add("created_by", "Vishnu Polu")
core.Tags.of(ref_implementation_stack).add("Domain", "glue")
core.Tags.of(ref_implementation_stack).add("Env", deploysettings.environment)

app.synth()
