from __future__ import annotations

from pathlib import Path

from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    SecretValue,
    Stack,
)
from constructs import Construct

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_logs as logs
from aws_cdk import aws_secretsmanager as secretsmanager


class CmrCareEcsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cmr_mcp_url = self.node.try_get_context("cmrMcpUrl")
        openai_secret_name = self.node.try_get_context("openaiSecretName")
        openai_api_key = self.node.try_get_context("openaiApiKey")

        vpc = ec2.Vpc(
            self,
            "CmrCareVpc",
            max_azs=2,
        )

        cluster = ecs.Cluster(
            self,
            "CmrCareCluster",
            vpc=vpc,
        )

        repo_root = Path(__file__).resolve().parents[1]
        image_asset = ecr_assets.DockerImageAsset(
            self,
            "CmrCareImage",
            directory=str(repo_root),
            platform=ecr_assets.Platform.LINUX_AMD64,
        )

        log_group = logs.LogGroup(
            self,
            "CmrCareLogs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        env_vars = {
            "APP_HOST": "0.0.0.0",
            "APP_PORT": "8000",
        }
        if cmr_mcp_url:
            env_vars["CMR_MCP_URL"] = cmr_mcp_url

        secrets: dict[str, ecs.Secret] = {}
        secret = None
        if openai_secret_name:
            secret = secretsmanager.Secret.from_secret_name_v2(
                self,
                "OpenAISecret",
                openai_secret_name,
            )
        else:
            secret_value = SecretValue.unsafe_plain_text(openai_api_key or "REPLACE_ME")
            secret = secretsmanager.Secret(
                self,
                "OpenAISecret",
                secret_name="cmr-care/openai-api-key",
                secret_string_value=secret_value,
            )
        if secret is not None:
            secrets["OPENAI_API_KEY"] = ecs.Secret.from_secrets_manager(secret)

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "CmrCareService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(image_asset),
                container_port=8000,
                environment=env_vars,
                secrets=secrets or None,
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="cmr-care",
                    log_group=log_group,
                ),
            ),
        )

        service.target_group.configure_health_check(path="/")

        if secret is not None:
            CfnOutput(
                self,
                "OpenAISecretName",
                value=secret.secret_name,
            )

        CfnOutput(
            self,
            "LoadBalancerURL",
            value=f"http://{service.load_balancer.load_balancer_dns_name}",
        )
