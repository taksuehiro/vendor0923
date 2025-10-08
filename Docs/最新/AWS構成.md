ベンダーRAG（ECS × Bedrock）アーキテクチャ最終版
1. 概要

目的：S3上のFAISSベクトルを用いたRAG検索APIを Fargate（ECS）で提供。埋め込みは Bedrock Titan v1。

フロント：Amplify（検証用）。

公開経路：api.3ii.biz → ALB (vendor0919-alb-new) → ECS サービス (vendor1007-2-service)。

ストレージ：s3://vendor-rag-bucket/faiss/index/（index.faiss / index.pkl）。


論理構造
[ユーザー] 
   ↓ HTTPS
[Amazon CloudFront / Amplify Hosting]
   ↓
[Application Load Balancer (ALB)]
   ↓
[Amazon ECS (Fargate)]
   └── vendor1007-2-api (FastAPI + LangChain)
         ├─ S3同期 (/tmp/vectorstore にDL)
         ├─ FAISSロード
         ├─ Bedrock Titan Embeddings 呼び出し
         └─ 検索API /search 提供
   ↓
[Amazon Bedrock]
   └── amazon.titan-embed-text-v1（ベクトル生成）

[Amazon S3]
   └── vendor-rag-bucket/faiss/index/
         ├─ index.faiss
         └─ index.pkl



2. 図（Mermaid）
flowchart LR
  User((User)) -- HTTPS --> DNS[Route 53 / 外部DNS<br/>api.3ii.biz]
  DNS -- CNAME --> ALB[ALB: vendor0919-alb-new<br/>443/TLS13<br/>/health]
  ALB -- forward:443 --> TG[Target Group: vendor1007-2-tg<br/>Port 8080]
  TG --> ECS[ECS (Fargate)<br/>Service: vendor1007-2-service<br/>TaskDef: vendor1007-2-task:4<br/>Container: vendor1007-2-api:8080]
  ECS -- GetObject/ListBucket --> S3[(S3<br/>vendor-rag-bucket<br/>faiss/index/)]
  ECS -- InvokeModel --> Bedrock[(Amazon Bedrock<br/>amazon.titan-embed-text-v1)]


※ api.3ii.biz のホストゾーンは別アカウント / 外部DNSの可能性あり（後述の取得手順参照）。

3. 実測パラメータ（抜粋）
3.1 エンドポイント / ALB

ALB DNS：vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com

スキーム：internet-facing

VPC：vpc-0484f20452b5a7773

サブネット：subnet-0d9d1c034ff3310ca, subnet-0fad2d28b04a7e2b5

ALB SG：sg-0fa3ee4b2af769436（inbound 443→0.0.0.0/0）

Listeners

:80 → HTTPS(443) にリダイレクト（HTTP_301）

:443 → TargetGroup vendor1007-2-tg へ forward

ACM：arn:aws:acm:ap-northeast-1:067717894185:certificate/a64da2db-df7e-4999-a221-761c13e49c9b

SSL Policy：ELBSecurityPolicy-TLS13-1-2-Res-2021-06

Target Group

ARN：arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor1007-2-tg/1c2274fe39e8711a

Port/Proto：8080 / HTTP

HealthCheckPath：/health（ヘルシー確認済み）

3.2 ECS（Fargate）

Cluster：vendor1007-2-cluster

Service：vendor1007-2-service

desired=1 / running=1

awsvpc

Subnets：subnet-0d9d1c034ff3310ca, subnet-0ae8225ddbc930c8b

SG：sg-023a5d27e13e2a967

Public IP：ENABLED

TaskDefinition：vendor1007-2-task:4

container：vendor1007-2-api（:8080）

Env：

S3_BUCKET_NAME=vendor-rag-bucket

S3_PREFIX=faiss/index

AWS_REGION=ap-northeast-1

BEDROCK_EMBEDDINGS_MODEL_ID=amazon.titan-embed-text-v1

Roles

TaskRole：arn:aws:iam::067717894185:role/ecsTaskRole

付与ポリシー：

AmazonBedrockFullAccess

AmazonS3ReadOnlyAccess

SecretsManagerReadWrite（必要なら見直し）

AmazonSSMManagedInstanceCore（必要性を要検討）

ExecutionRole：arn:aws:iam::067717894185:role/ecsTaskExecutionRole

3.3 S3（FAISS）

バケット：vendor-rag-bucket

プレフィックス：faiss/index/

オブジェクト（更新済み）

index.faiss（657,453 bytes, 2025-10-07 04:42:13）

index.pkl（53,546 bytes, 2025-10-07 04:42:13）

バケットポリシー：なし（IAM ロールで制御）

3.4 Bedrock（モデル）

amazon.titan-embed-text-v1（G1 Text）

amazon.titan-embed-text-v2:0 も一覧に存在（今回は未使用）

3.5 証明書（ACM）

Domain：api.3ii.biz

ARN：arn:aws:acm:ap-northeast-1:067717894185:certificate/a64da2db-df7e-4999-a221-761c13e49c9b

Status：ISSUED / InUse: true

Validity：2025-10-04 〜 2026-11-02

3.6 ログ（CloudWatch）

LogGroup：/ecs/vendor1007-2-api

直近ログ：/health 200 が継続、/ 404 は ALB のヘルスチェック/外部クローラ由来。

WebSocket 403 や POST /api/v1/orders 404 は無関係なクローラアクセスの可能性（運用でフィルタ可）。

4. 図面・添付の更新指針

図の注釈：

ALB DNS / ACM / Listener ポリシー（TLS1.3）

TG 8080 / HealthCheck /health

ECS（Service/TaskDef/Container名/Env）

TaskRole/ExecutionRole の分離と付与ポリシー

S3 パスとオブジェクト名（更新日時）

Bedrock モデル ID

付帯資料（JSON）：arch_snapshot.json を格納しておくと監査・再現性に有用。

5. 追加で取りに行くべき情報（取得方法）
5.1 Route 53 / DNS（api.3ii.biz が別アカウント・外部DNSの可能性）

あなたのアカウントでは HostedZone が見つからなかったため、以下で現行の委譲先を確認：

# CloudShell（nslookup/dig が使える前提）
nslookup -type=SOA 3ii.biz
nslookup -type=CNAME api.3ii.biz
# or
dig SOA 3ii.biz +short
dig CNAME api.3ii.biz +short


確認ポイント

api.3ii.biz の CNAME が ALB DNS に向いているか
例）api.3ii.biz. CNAME vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com.

SOA/NS がどの DNS プロバイダか（Route53 でない可能性あり）

別アカウントの Route53 を使っている場合は、そのアカウントで HostedZone を取得してください。

もし将来 正式ドメイン（例：api.ttcdx.co.jp）へ移行するなら、同じ手順で CNAME と ACM を差し替えればOK。

5.2 ACM の ALB バインド先の明示（任意）

InUseBy を明示したい場合（証明書ARNを CERT_ARN にセットして）：

CERT_ARN="arn:aws:acm:ap-northeast-1:067717894185:certificate/a64da2db-df7e-4999-a221-761c13e49c9b"
aws acm describe-certificate --certificate-arn "$CERT_ARN" --region "$REGION" \
  --query "Certificate.InUseBy" --output json

5.3 ECS ENI / 実IP（運用付録に）

Fargate タスクの ENI ID / Private IP を載せたい場合：

aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" --region "$REGION" --output text
TASK_ARN="<上の出力の任意1件>"
aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" --region "$REGION" \
  --query "tasks[0].attachments[0].details" --output table

# ENI IDが分かったら
ENI_ID="<上の出力で 'networkInterfaceId' の値>"
aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" --region "$REGION" \
  --query "NetworkInterfaces[0].{PrivateIp:PrivateIpAddress,Subnet:SubnetId,SGs:Groups[*].GroupId}" --output json

5.4 セキュリティグループ（ECS側）

ECS サービス側の SG 詳細を図に載せる場合：

ECS_SG=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --region "$REGION" \
  --query "services[0].networkConfiguration.awsvpcConfiguration.securityGroups[0]" --output text)

aws ec2 describe-security-groups --group-ids "$ECS_SG" --region "$REGION" \
  --query "SecurityGroups[0].{GroupId:GroupId,Name:GroupName,Ingress:IpPermissions,Egress:IpPermissionsEgress}" --output json

6. 監視・保守で使う定番コマンド（付録）
# ALB → TG のヘルス
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" --region "$REGION" \
  --query "TargetHealthDescriptions[*].{ID:Target.Id,State:TargetHealth.State,Reason:TargetHealth.Reason}" --output table

# ECS デプロイ状況
aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --region "$REGION" \
  --query "services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,rollouts:deployments[*].rolloutState}" --output table

# 直近ログ
aws logs describe-log-streams --log-group-name "$LOG_GROUP" --order-by LastEventTime --descending --limit 1 --query "logStreams[0].logStreamName" --output text | \
xargs -I{} aws logs get-log-events --log-group-name "$LOG_GROUP" --log-stream-name "{}" --limit 100 --query 'events[*].message' --output text

7. 最終チェックリスト

 ALB 443 → TG(8080) / /health OK

 TaskRole に AmazonBedrockFullAccess / AmazonS3ReadOnlyAccess

 BEDROCK_EMBEDDINGS_MODEL_ID=amazon.titan-embed-text-v1

 S3 の index.faiss / index.pkl（Titan v1で再生成済み）

 api.3ii.biz → ALB CNAME（DNS 側の設定主体を明記）

メモ（運用上の注意）

/ への 404 や PROPFIND、未知のパスはクローラ由来のため問題なし。必要に応じてWAFやALBルールで遮断。

SecretsManagerReadWrite 等の広い権限は、実際に利用していなければ 権限縮小を推奨。