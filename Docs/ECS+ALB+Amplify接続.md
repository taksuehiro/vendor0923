ECS(Fargate) + ALB + Amplify 接続 手順 & トラブルシュート（実録）

実行環境：AWS CloudShell（東京 / ap-northeast-1） リポジトリ：taksuehiro/vendor0919 バックエンド：FastAPI（uvicorn, port 8080）

0. 主要リソース（最終形）

AWS Account: 067717894185

ECR: 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest

ECS Cluster: vendor0919-cluster

Task Definition: vendor0919-task （v1→v2）

Service: vendor0919-service（Fargate, awsvpc, desired=1）

VPC: vpc-0484f20452b5a7773（10.0.0.0/16）

Subnets (Public):

subnet-0d9d1c034ff3310ca（az=1a, CIDR=10.0.2.0/24）

subnet-0fad2d28b04a7e2b5（az=1c, CIDR=10.0.10.0/24）※今回新規作成

Security Groups:

ECSタスク用：sg-023a5d27e13e2a967（既存流用 / 別名: vendor0918-sg）

ALB用：sg-0fa3ee4b2af769436（今回新規 / 80開放）

ALB: vendor0919-alb

ARN: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:loadbalancer/app/vendor0919-alb/bd4f77a211c27373

DNS: vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com

Target Group: vendor0919-tg（HTTP:8080, target-type=ip）

ARN: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg/09902b0116e2f1dd

HealthCheck: GET /health（200）

Listener: HTTP:80 → vendor0919-tg

Amplify ENV:

AMPLIFY_MONOREPO_APP_ROOT=frontend

NEXT_PUBLIC_API_BASE=http://vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com

1. バックエンド（FastAPI）をコンテナ化 → ECR へ push
1-1. Dockerfile（backend/）
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
1-2. Build & ローカル起動テスト
cd backend


docker build -t vendor0919-api:latest .


docker run -d -p 8080:8080 --name vendor0919-test vendor0919-api:latest
curl http://localhost:8080/health   # => {"status":"ok"}
docker stop vendor0919-test && docker rm vendor0919-test
1-3. ECR 作成 & push
aws ecr create-repository --repository-name vendor0919-api --region ap-northeast-1
aws ecr get-login-password --region ap-northeast-1 \
  | docker login --username AWS --password-stdin 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com


docker tag vendor0919-api:latest 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest
docker push 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest
2. ECS(Fargate) 構築
2-1. クラスター
aws ecs create-cluster --cluster-name vendor0919-cluster --region ap-northeast-1
2-2. TaskDef（最初は healthCheck あり）
{
  "family": "vendor0919-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::067717894185:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest",
      "portMappings": [{ "containerPort": 8080, "protocol": "tcp" }],
      "essential": true,
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vendor0919-api",
          "awslogs-region": "ap-northeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
2-3. 最初のハマり：タスク即死（CloudWatch Logs が無い）

症状：stoppedReason = ResourceInitializationError: ... Cloudwatch log group does not exist

対処：先にロググループを作る

aws logs create-log-group --log-group-name /ecs/vendor0919-api --region ap-northeast-1
2-4. サービス（暫定：Public IP 直アクセスで起動テスト）
aws ecs create-service \
  --cluster vendor0919-cluster \
  --service-name vendor0919-service \
  --task-definition vendor0919-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0d9d1c034ff3310ca,subnet-0ae8225ddbc930c8b],securityGroups=[sg-023a5d27e13e2a967],assignPublicIp=ENABLED}" \
  --region ap-northeast-1

2ndハマり：Task failed container health checks → 起動はしてるがヘルスチェック間に合わず落ちる

対処A（検証優先）：healthCheck を一旦外した TaskDef v2 を登録 → --force-new-deployment

# healthCheck を外した taskdef-nohealth.json を登録
aws ecs register-task-definition --cli-input-json file://taskdef-nohealth.json --region ap-northeast-1
aws ecs update-service \
  --cluster vendor0919-cluster \
  --service vendor0919-service \
  --task-definition vendor0919-task \
  --force-new-deployment \
  --region ap-northeast-1

タスクの Public IP で疎通：

TASK_ARN=$(aws ecs list-tasks --cluster vendor0919-cluster --service-name vendor0919-service --region ap-northeast-1 --query taskArns[0] --output text)
ENI_ID=$(aws ecs describe-tasks --cluster vendor0919-cluster --tasks $TASK_ARN --region ap-northeast-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region ap-northeast-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)


# SG に 8080 を開けてからテスト
aws ec2 authorize-security-group-ingress --group-id sg-023a5d27e13e2a967 --protocol tcp --port 8080 --cidr 0.0.0.0/0 --region ap-northeast-1
curl http://$PUBLIC_IP:8080/health   # => {"status":"ok"}
3. ALB 構築（本命）
3-1. 3rdハマり：ALB は同一AZの複数サブネットを受け付けない

既存 Public Subnet が両方 1a だったためエラー。

対処：ap-northeast-1c に Public Subnet 追加 → MapPublicIpOnLaunch 有効化

aws ec2 create-subnet \
  --vpc-id vpc-0484f20452b5a7773 \
  --cidr-block 10.0.10.0/24 \
  --availability-zone ap-northeast-1c \
  --region ap-northeast-1


aws ec2 modify-subnet-attribute --subnet-id subnet-0fad2d28b04a7e2b5 --map-public-ip-on-launch --region ap-northeast-1
# （既存の 1a 側サブネットも念のため public 化を確認）
3-2. SG, ALB, TG, Listener の作成
# ALB用SG（80開放）
aws ec2 create-security-group --group-name vendor0919-alb-sg --description "ALB for vendor0919" --vpc-id vpc-0484f20452b5a7773 --region ap-northeast-1
aws ec2 authorize-security-group-ingress --group-id sg-0fa3ee4b2af769436 --protocol tcp --port 80 --cidr 0.0.0.0/0 --region ap-northeast-1


# ALB
aws elbv2 create-load-balancer \
  --name vendor0919-alb \
  --subnets subnet-0d9d1c034ff3310ca subnet-0fad2d28b04a7e2b5 \
  --security-groups sg-0fa3ee4b2af769436 \
  --scheme internet-facing \
  --type application \
  --region ap-northeast-1


# Target Group（8080, IP ターゲット）
aws elbv2 create-target-group \
  --name vendor0919-tg \
  --protocol HTTP \
  --port 8080 \
  --vpc-id vpc-0484f20452b5a7773 \
  --target-type ip \
  --region ap-northeast-1


# Listener（80→TG）
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:loadbalancer/app/vendor0919-alb/bd4f77a211c27373 \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg/09902b0116e2f1dd \
  --region ap-northeast-1
3-3. 4thハマり：ALB ヘルスチェック unhealthy (Target.Timeout)

原因①：TG の HealthCheckPath が / だった（アプリは /health）

原因②：ECS SG の 8080 に ALB SG からの通信が未許可

対処：

# TG のヘルスチェックを /health に修正
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg/09902b0116e2f1dd \
  --health-check-path /health \
  --region ap-northeast-1


# ECS SG に ALB SG からの 8080 を許可
aws ec2 authorize-security-group-ingress \
  --group-id sg-023a5d27e13e2a967 \
  --protocol tcp \
  --port 8080 \
  --source-group sg-0fa3ee4b2af769436 \
  --region ap-northeast-1


# => しばらくして healthy に遷移
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg/09902b0116e2f1dd --region ap-northeast-1
3-4. ALB 経由の疎通
curl http://vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com/health
# => {"status":"ok"}
# ※ 作成直後は DNS 伝播で数十秒〜数分かかることがある（最初は無応答→後からOKになった）
4. Amplify 側の設定

環境変数：

AMPLIFY_MONOREPO_APP_ROOT=frontend
NEXT_PUBLIC_API_BASE=http://vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com

注意：http:// を忘れるとフロントからの fetch が失敗する（実際に抜けてて直した）

Console から Save and redeploy 実行

フロント → バック疎通 OK（PoC 完了）

補足：Amplify の 404 は後日対応（build 設定/出力ディレクトリの見直し）

5. トラブルと解決（要点だけ早見表）
症状	原因	解決
タスク即 STOP（ログ無し）	CloudWatch Log Group 未作成	/ecs/vendor0919-api を 先に作成
Task failed container health checks	起動に時間 > startPeriod / ヘルスチェック厳しめ	いったん healthCheck 無効で起動 → 後で startPeriod 長めに調整
ALB 作成エラー：同一AZサブネット	ALB は AZ ごとに 1 サブネット必要	別AZ（1c）に Public Subnet 新規作成
TG unhealthy (Target.Timeout)	HealthCheckPath / ミスマッチ / SG 未許可	TG を /health に変更 + ALB→ECS(8080) 許可
curl http://ALB/health 無応答	DNS 伝播中/直後	数十秒〜数分で解消。-v で追跡
フロントから API 叩けない	NEXT_PUBLIC_API_BASE に http:// 抜け	フルURLに修正して再デプロイ
6. 便利コマンド集
# サービスの状態
aws ecs describe-services --cluster vendor0919-cluster --services vendor0919-service --region ap-northeast-1 --query 'services[0].{running:runningCount,pending:pendingCount}'


# タスク → ENI → Public IP
aws ecs list-tasks --cluster vendor0919-cluster --service vendor0919-service --region ap-northeast-1
aws ecs describe-tasks --cluster vendor0919-cluster --tasks <TASK_ARN> --region ap-northeast-1 --query 'tasks[0].attachments[0].details'
aws ec2 describe-network-interfaces --network-interface-ids <ENI_ID> --region ap-northeast-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text


# Target Health
aws elbv2 describe-target-health --target-group-arn <TG_ARN> --region ap-northeast-1


# Listener 確認
aws elbv2 describe-listeners --load-balancer-arn <ALB_ARN> --region ap-northeast-1
7. 次やるなら（本番向け）

HTTPS 化：ACM 証明書発行 → 443 リスナー作成 → SG(443) 開放 → NEXT_PUBLIC_API_BASE=https://...

Auto Scaling：ALB リクエスト/CPUでスケールアウト

監視：CloudWatch Logs & Metrics, ALB アクセスログ（S3）

セキュリティ最小化：直叩き用の 8080 0.0.0.0/0 は閉じ、ALB → ECS のみ許可

8. 付録：ID一覧（コピペ用）

Account: 067717894185

ECR: 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest

Cluster: vendor0919-cluster

TaskDef: vendor0919-task:1 / vendor0919-task:2

Service: vendor0919-service

VPC: vpc-0484f20452b5a7773

Subnets: subnet-0d9d1c034ff3310ca（1a）, subnet-0fad2d28b04a7e2b5（1c）

SG(ECS): sg-023a5d27e13e2a967

SG(ALB): sg-0fa3ee4b2af769436

ALB ARN: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:loadbalancer/app/vendor0919-alb/bd4f77a211c27373

ALB DNS: vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com

TG ARN: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg/09902b0116e2f1dd

Listener ARN: arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:listener/app/vendor0919-alb/bd4f77a211c27373/6ef43367ca107d58