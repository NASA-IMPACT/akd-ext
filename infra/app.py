#!/usr/bin/env python3
from __future__ import annotations

import os

import aws_cdk as cdk

from stack import CmrCareEcsStack


app = cdk.App()

CmrCareEcsStack(
    app,
    "CmrCareEcsStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
