import json
import pulumi
import pulumi_aws as aws


# VPC
vpc = aws.ec2.Vpc("poridhi-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={'Name': 'poridhi-vpc'}
)

# Internet Gateway
internet_gateway = aws.ec2.InternetGateway("poridhi-igw",
    vpc_id=vpc.id,
)

# Public Subnet
subnet = aws.ec2.Subnet("poridhi-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True
)

# Route Table
route_table = aws.ec2.RouteTable("poridhi-route-table",
    vpc_id=vpc.id,
    routes=[aws.ec2.RouteTableRouteArgs(
        cidr_block="0.0.0.0/0",
        gateway_id=internet_gateway.id,
    )]
)

# Route Table Association
route_table_association = aws.ec2.RouteTableAssociation(
    "poridhi-rt-association",
    subnet_id=subnet.id,
    route_table_id=route_table.id
)

# Security Group
security_group = aws.ec2.SecurityGroup("poridhi-security-group",
    description="Security group allowing all traffic",
    vpc_id=vpc.id,
    ingress=[
        {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ["0.0.0.0/0"]}
    ],
    egress=[
        {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
    ]
)

# S3 Bucket
models_bucket = aws.s3.Bucket("customer-churn-model-bucket",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
)

# IAM Role for EC2
ec2_role = aws.iam.Role("ec2-s3-access-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    })
)

# IAM Policy for S3 Access
s3_policy = aws.iam.Policy("s3-access-policy",
    policy=models_bucket.id.apply(lambda bucket_name: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ]
        }]
    }))
)

# Attach S3 policy to IAM role
s3_policy_attachment = aws.iam.RolePolicyAttachment("s3-policy-attachment",
    role=ec2_role.name,
    policy_arn=s3_policy.arn
)

# Create Instance Profile
instance_profile = aws.iam.InstanceProfile("ec2-instance-profile",
    role=ec2_role.name
)

# EC2 Instance with IAM Instance Profile
server_instance = aws.ec2.Instance('server_instance',
    instance_type='t3.small',
    ami='ami-01811d4912b4ccb26',
    vpc_security_group_ids=[security_group.id],
    subnet_id=subnet.id,
    key_name='key-pair-poridhi-poc',
    iam_instance_profile=instance_profile.name,
    ebs_block_devices=[
        aws.ec2.InstanceEbsBlockDeviceArgs(
            device_name="/dev/sda1",
            volume_type="gp3",
            volume_size=20,
            delete_on_termination=True,
        ),
    ],
    tags={'Name': 'server_instance'}
)

# Outputs
pulumi.export('server_instance_public_ip', server_instance.public_ip)
pulumi.export('models_bucket_name', models_bucket.id)