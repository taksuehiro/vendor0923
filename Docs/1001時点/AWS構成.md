## Amplify Apps
- AppId: dcs5uerijxlhh
  DefaultDomain: dcs5uerijxlhh.amplifyapp.com
  Name: vendor0923
  Platform: WEB_COMPUTE
  Repo: https://github.com/taksuehiro/vendor0923

### 各アプリのブランチ
- AppId: dcs5uerijxlhh
- Enabled: true
  LastBuild: null
  Name: main
  Stage: PRODUCTION

## S3 Buckets (prefix: vendor)
vendor-rag-0919
vendor0913-documents
vendor0919-alb-logs

- Cluster: arn:aws:ecs:ap-northeast-1:067717894185:cluster/vendor0919-cluster
- Desired: 1
- Running: 1
- SGs:
- - sg-023a5d27e13e2a967
- Service: vendor0919-service
- Status: ACTIVE
- Subnets:
- - subnet-0d9d1c034ff3310ca
- - subnet-0ae8225ddbc930c8b
- TGArns:
- - arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg-new/1082e69f886174a0
- TaskDef: arn:aws:ecs:ap-northeast-1:067717894185:task-definition/vendor0919-task:56

### Task Definition Detail
Containers:
- Command: null
  Env:
  - name: SOURCE
    value: s3
  - name: S3
    value: vendor-rag-0919/vectorstore/prod
  - name: BEDROCK_REGION
    value: ap-northeast-1
  - name: LOCAL_DIR
    value: /app/vectorstore
  Image: 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest
  Name: api
  PortMappings:
  - containerPort: 8080
    hostPort: 8080
    protocol: tcp
Cpu: '1024'
ExecRole: arn:aws:iam::067717894185:role/ecsTaskExecutionRole-vendor0919
Family: vendor0919-task
Memory: '2048'
NetworkMode: awsvpc
Requires:
- FARGATE
Revision: 56
TaskRole: arn:aws:iam::067717894185:role/ecsTaskRole-vendor0919

### Security Groups (ECS Service)
- Desc: Allow 8080 for ECS
- GroupId: sg-023a5d27e13e2a967
- GroupName: vendor0918-sg
- VpcId: vpc-0484f20452b5a7773

### Security Groups (ALB)
- Desc: ALB for vendor0919
- GroupId: sg-0fa3ee4b2af769436
- GroupName: vendor0919-alb-sg
- VpcId: vpc-0484f20452b5a7773

## ALB / Listeners / Rules / Target Group
- ALB DNS: vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com
Name: vendor0919-alb-new
Scheme: internet-facing
State: active
Subnets:
- subnet-0d9d1c034ff3310ca
- subnet-0fad2d28b04a7e2b5
### Listeners
- Certificates: null
  DefaultActions:
  - ForwardConfig:
      TargetGroupStickinessConfig:
        Enabled: false
      TargetGroups:
      - TargetGroupArn: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg-new/1082e69f886174a0
        Weight: 1
    TargetGroupArn: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg-new/1082e69f886174a0
    Type: forward
  ListenerArn: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:listener/app/vendor0919-alb-new/95a759899fe9fe00/b8b2579af9dddae8
  Port: 80
  Protocol: HTTP
### Rules (per Listener)
- arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:listener/app/vendor0919-alb-new/95a759899fe9fe00/b8b2579af9dddae8
- Actions:
  - ForwardConfig:
      TargetGroupStickinessConfig:
        Enabled: false
      TargetGroups:
      - TargetGroupArn: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg-new/1082e69f886174a0
        Weight: 1
    TargetGroupArn: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg-new/1082e69f886174a0
    Type: forward
  Conditions: []
  Priority: default
### Target Group (Health Settings)
HealthPath: /health
HealthPort: traffic-port
Matcher: '200'
Name: vendor0919-tg-new
Port: 8080
Protocol: HTTP
### Target Health
-----------------------------------------------------------------------
|                        DescribeTargetHealth                         |
+------+-----------------------------------+-----------+--------------+
| Port |              Reason               |   State   |   Target     |
+------+-----------------------------------+-----------+--------------+
|  8080|  Target.DeregistrationInProgress  |  draining |  10.0.2.168  |
|  8080|  None                             |  healthy  |  10.0.1.36   |
+------+-----------------------------------+-----------+--------------+

## VPC / Subnets (focused)
- VPC: vpc-0484f20452b5a7773
Cidr: 10.0.0.0/16
Tags: null
VpcId: vpc-0484f20452b5a7773
### Subnets used by ALB
- AZ: ap-northeast-1a
- Cidr: 10.0.2.0/24
- SubnetId: subnet-0d9d1c034ff3310ca
- Tags: null
- AZ: ap-northeast-1c
- Cidr: 10.0.10.0/24
- SubnetId: subnet-0fad2d28b04a7e2b5
- Tags: null
### Subnets used by ECS Service
- AZ: ap-northeast-1a
- Cidr: 10.0.2.0/24
- SubnetId: subnet-0d9d1c034ff3310ca
- Tags: null
- AZ: ap-northeast-1a
- Cidr: 10.0.1.0/24
- SubnetId: subnet-0ae8225ddbc930c8b
- Tags: null

# 現状サマリー（vendor0919）
- Cluster: vendor0919-cluster
- Service: vendor0919-service
- TaskDef: vendor0919-task:56
- ALB    : 95a759899fe9fe00
- ALB DNS: vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com
- TG     : 1082e69f886174a0
- Amplify: dcs5uerijxlhh.amplifyapp.com (AppId: dcs5uerijxlhh)



## Bedrock 構成 (ap-northeast-1)

### Model Invocation Logging

### Provisioned Model Throughputs
- []

### Custom Models

### Model Customization Jobs (Fine-tune/続行学習)

### Bedrock Agents
- []

### Bedrock Agent Aliases

### Bedrock Knowledge Bases
- []

#### Knowledge Base Details & Data Sources

### VPC Interface Endpoints for Bedrock
- []