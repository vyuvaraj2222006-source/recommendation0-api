"""
STEP 4: CLOUD DEPLOYMENT SCRIPT (AWS)
=====================================
Deploy the recommendation API to AWS using ECS/Fargate
"""

import boto3
import json
import os
import time

class AWSDeployer:
    """
    Deploy recommendation system to AWS ECS/Fargate
    """
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ecs = boto3.client('ecs', region_name=region)
        self.ecr = boto3.client('ecr', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        
    def create_ecr_repository(self, repo_name='recommendation-api'):
        """
        Step 4.1: Create ECR repository for Docker images
        """
        try:
            response = self.ecr.create_repository(
                repositoryName=repo_name,
                imageScanningConfiguration={'scanOnPush': True}
            )
            repository_uri = response['repository']['repositoryUri']
            print(f" ECR Repository created: {repository_uri}")
            return repository_uri
        except self.ecr.exceptions.RepositoryAlreadyExistsException:
            response = self.ecr.describe_repositories(repositoryNames=[repo_name])
            repository_uri = response['repositories'][0]['repositoryUri']
            print(f"ECR Repository exists: {repository_uri}")
            return repository_uri
    
    def push_docker_image(self, repository_uri, local_image='recommendation-api:latest'):
        """
        Step 4.2: Push Docker image to ECR
        
        Run these commands locally:
        """
        account_id = repository_uri.split('.')[0]
        
        commands = f"""
# Build the Docker image
docker build -t {local_image} .

# Login to ECR
aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{self.region}.amazonaws.com

# Tag the image
docker tag {local_image} {repository_uri}:latest

# Push to ECR
docker push {repository_uri}:latest
        """
        
        print("\n" + "="*60)
        print("Run these commands to push your Docker image:")
        print("="*60)
        print(commands)
        print("="*60 + "\n")
        
        return f"{repository_uri}:latest"
    
    def create_ecs_cluster(self, cluster_name='recommendation-cluster'):
        """
        Step 4.3: Create ECS Cluster
        """
        try:
            response = self.ecs.create_cluster(
                clusterName=cluster_name,
                capacityProviders=['FARGATE', 'FARGATE_SPOT']
            )
            print(f"ECS Cluster created: {cluster_name}")
            return cluster_name
        except Exception as e:
            if 'already exists' in str(e):
                print(f" ECS Cluster exists: {cluster_name}")
                return cluster_name
            raise
    
    def create_task_definition(self, image_uri, task_family='recommendation-task'):
        """
        Step 4.4: Create ECS Task Definition
        """
        task_definition = {
            "family": task_family,
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "1024",  # 1 vCPU
            "memory": "2048",  # 2 GB
            "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole",  # Replace with your role
            "containerDefinitions": [
                {
                    "name": "recommendation-api",
                    "image": image_uri,
                    "portMappings": [
                        {
                            "containerPort": 5000,
                            "protocol": "tcp"
                        }
                    ],
                    "environment": [
                        {"name": "FLASK_ENV", "value": "production"},
                        {"name": "REDIS_HOST", "value": "YOUR_REDIS_ENDPOINT"}  # Configure Redis
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/recommendation-api",
                            "awslogs-region": self.region,
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 60
                    }
                }
            ]
        }
        
        response = self.ecs.register_task_definition(**task_definition)
        task_def_arn = response['taskDefinition']['taskDefinitionArn']
        print(f"Task Definition created: {task_def_arn}")
        return task_def_arn
    
    def create_load_balancer(self, vpc_id, subnet_ids, security_group_id):
        """
        Step 4.5: Create Application Load Balancer
        """
        # Create load balancer
        response = self.elbv2.create_load_balancer(
            Name='recommendation-alb',
            Subnets=subnet_ids,
            SecurityGroups=[security_group_id],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4'
        )
        
        lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
        lb_dns = response['LoadBalancers'][0]['DNSName']
        print(f"Load Balancer created: {lb_dns}")
        
        # Create target group
        tg_response = self.elbv2.create_target_group(
            Name='recommendation-tg',
            Protocol='HTTP',
            Port=5000,
            VpcId=vpc_id,
            TargetType='ip',
            HealthCheckPath='/health',
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=3
        )
        
        tg_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
        print(f" Target Group created")
        
        # Create listener
        self.elbv2.create_listener(
            LoadBalancerArn=lb_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': tg_arn
                }
            ]
        )
        print(f"Listener created")
        
        return lb_arn, tg_arn, lb_dns
    
    def create_ecs_service(self, cluster_name, task_definition_arn, target_group_arn, 
                          subnet_ids, security_group_id, service_name='recommendation-service'):
        """
        Step 4.6: Create ECS Service
        """
        response = self.ecs.create_service(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=task_definition_arn,
            desiredCount=2,  # Run 2 instances for high availability
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnet_ids,
                    'securityGroups': [security_group_id],
                    'assignPublicIp': 'ENABLED'
                }
            },
            loadBalancers=[
                {
                    'targetGroupArn': target_group_arn,
                    'containerName': 'recommendation-api',
                    'containerPort': 5000
                }
            ],
            healthCheckGracePeriodSeconds=60
        )
        
        print(f" ECS Service created: {service_name}")
        return response['service']['serviceArn']
    
    def deploy_full_stack(self):
        """
        Step 4.7: Complete deployment orchestration
        """
        print("\n" + "="*60)
        print("DEPLOYING RECOMMENDATION SYSTEM TO AWS")
        print("="*60 + "\n")
        
        # Step 1: Create ECR Repository
        print("Step 1: Creating ECR Repository...")
        repository_uri = self.create_ecr_repository()
        
        # Step 2: Instructions to push Docker image
        print("\nStep 2: Push Docker Image...")
        image_uri = self.push_docker_image(repository_uri)
        
        print("\nPress Enter after you've pushed the Docker image...")
        input()
        
        # Step 3: Create ECS Cluster
        print("\nStep 3: Creating ECS Cluster...")
        cluster_name = self.create_ecs_cluster()
        
        # Step 4: Create Task Definition
        print("\nStep 4: Creating Task Definition...")
        task_def_arn = self.create_task_definition(image_uri)
        
        print("\n" + "="*60)
        print("DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"ECR Repository: {repository_uri}")
        print(f"ECS Cluster: {cluster_name}")
        print(f"Task Definition: {task_def_arn}")
        print("\nNext steps:")
        print("1. Configure VPC, subnets, and security groups")
        print("2. Set up Redis cache (ElastiCache)")
        print("3. Create load balancer and ECS service")
        print("4. Configure auto-scaling")
        print("="*60 + "\n")


# SIMPLIFIED DEPLOYMENT COMMANDS
def print_deployment_commands():
    """
    Step 4.8: Simplified AWS CLI deployment commands
    """
    commands = """
# ============================================
# AWS DEPLOYMENT COMMANDS (Run in terminal)
# ============================================

# 1. Configure AWS CLI
aws configure

# 2. Create ECR repository
aws ecr create-repository --repository-name recommendation-api --region us-east-1

# 3. Build and push Docker image
$(aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com)
docker build -t recommendation-api .
docker tag recommendation-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/recommendation-api:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/recommendation-api:latest

# 4. Create ECS cluster
aws ecs create-cluster --cluster-name recommendation-cluster --region us-east-1

# 5. Register task definition (create task-definition.json first)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 6. Create ECS service
aws ecs create-service \\
  --cluster recommendation-cluster \\
  --service-name recommendation-service \\
  --task-definition recommendation-task \\
  --desired-count 2 \\
  --launch-type FARGATE \\
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}"

# 7. Get service status
aws ecs describe-services --cluster recommendation-cluster --services recommendation-service
    """
    print(commands)


if __name__ == "__main__":
    """
    Run deployment
    """
    print("\nChoose deployment method:")
    print("1. Automated Python deployment")
    print("2. Show AWS CLI commands")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        deployer = AWSDeployer(region='us-east-1')
        deployer.deploy_full_stack()
    else:
        print_deployment_commands()
