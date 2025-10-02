import aws_cdk as cdk
from dotenv import load_dotenv
import os
from dspm_els_stack import DspmEksStack

load_dotenv(dotenv_path="../.env")

account = os.getenv("AWS_ACCOUNT_ID")
region = os.getenv("AWS_REGION")

app = cdk.App()
DspmEksStack(app, "DspmEksStack",
    env=cdk.Environment(
        account=account,
        region=region
    )
)

app.synth()
