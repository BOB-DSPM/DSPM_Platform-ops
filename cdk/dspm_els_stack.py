import os
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_iam as iam,
    aws_rds as rds,
    aws_secretsmanager as secrets,
    Duration,
)


class DspmEksStack(Stack):
    def __init__(self, scope: Construct, construct_id:str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self, "DspmVpc",
            max_azs=2,
            nat_gateways=2,  # Multi-AZ 이중화를 위한 NAT Gateway 2개
        )

        admin_role_arn = os.getenv("EKS_ADMIN_ROLE_ARN")
        admin_role = None
        if admin_role_arn:
            admin_role = iam.Role.from_role_arn(self, "EksAdminRole", "arn:aws:iam::651706765732:role/EksAdminRole")

        # EKS Cluster
        cluster = eks.Cluster(
            self, "DspmEksCluster",
            vpc=vpc,
            version=eks.KubernetesVersion.V1_29,
            default_capacity=2,
            default_capacity_instance=ec2.InstanceType("t3.medium"),
            prune=False,
            masters_role=admin_role,
        )

        # RDS Database Secret
        db_secret = secrets.Secret(
            self, "DspmDbSecret",
            description="DSPM Database credentials",
            generate_secret_string=secrets.SecretStringGenerator(
                secret_string_template='{"username": "dspm_user"}',
                generate_string_key="password",
                exclude_characters=' %+~`#$&*()|[]{}:;<>?!\'/@"\\',
                password_length=32
            )
        )

        # RDS Security Group
        rds_security_group = ec2.SecurityGroup(
            self, "DspmRdsSecurityGroup",
            vpc=vpc,
            description="Security group for DSPM RDS instance",
            allow_all_outbound=False
        )

        # Allow inbound from EKS cluster security group
        rds_security_group.add_ingress_rule(
            peer=cluster.cluster_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from EKS cluster"
        )

        # RDS Subnet Group
        db_subnet_group = rds.SubnetGroup(
            self, "DspmDbSubnetGroup",
            description="Subnet group for DSPM RDS",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        )

        # RDS PostgreSQL Instance
        database = rds.DatabaseInstance(
            self, "DspmDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_14
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            subnet_group=db_subnet_group,
            security_groups=[rds_security_group],
            credentials=rds.Credentials.from_secret(db_secret),
            database_name="dspm",
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            backup_retention=Duration.days(7),
            deletion_protection=False,  # Set to True for production
            delete_automated_backups=True,
            multi_az=False,  # Set to True for production
            publicly_accessible=False,
            enable_performance_insights=False,  # Set to True for monitoring
        )
