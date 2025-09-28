0) ねらい（最終構成）

API Gateway (HTTP API v2)：$default ルートのみ、HTTP_PROXY で ALB直URIにプロキシ

CORS：FastAPI 側で許可（*/credentials 無し）、API Gateway 側でも CORS 有効（プレフライト安定化）

Amplify → API Gateway → ALB → ECS(FastAPI) が安定

1) CloudShell：環境変数 & ユーティリティ（コピペOK）
1-1. 共通環境変数（1回だけ）
cat > ~/.ttcdx_env.sh <<'EOF'
# ===== TTCDX/0919 環境（CloudShell用）=====
export AWS_REGION="ap-northeast-1"
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo 067717894185)"

# ---- ECR/ECS ----
export ECR_REPO="vendor0919-api"
export IMAGE_TAG_DEFAULT="6050c3f"
export CLUSTER="vendor0919-cluster"
export SERVICE="vendor0919-service"
export TASK_FAMILY="vendor0919-task"

# ---- ALB/TG ----
export ALB_DNS="vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com"
export TG_ARN="arn:aws:elasticloadbalancing:ap-northeast-1:067717894185:targetgroup/vendor0919-tg-new/1082e69f886174a0"

# ---- API Gateway (HTTP API v2) ----
export API_ID="5oxz71no0m"
export APIGW_ROUTE_ID=""
export APIGW_INTEGRATION_ID=""

# ---- ECR 完全名 ----
export ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

# PATH
mkdir -p ~/bin
export PATH="$HOME/bin:$PATH"
EOF

source ~/.ttcdx_env.sh
grep -q '.ttcdx_env.sh' ~/.bashrc || echo 'source ~/.ttcdx_env.sh' >> ~/.bashrc

1-2. ttc-resolve（最新状況を“記憶＆表示”）
cat > ~/bin/ttc-resolve <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
source ~/.ttcdx_env.sh

echo "==[Resolve] Basic context=="
echo "ACCOUNT_ID=${ACCOUNT_ID}"
echo "AWS_REGION=${AWS_REGION}"
echo "CLUSTER=${CLUSTER}  SERVICE=${SERVICE}"
echo "API_ID=${API_ID}"
echo

echo "==[Resolve] ECS service status=="
aws ecs describe-services \
  --cluster "${CLUSTER}" \
  --services "${SERVICE}" \
  --query 'services[0].{TaskDef:taskDefinition,Desired:desiredCount,Running:runningCount,Pending:pendingCount}' \
  --output table || true
echo

LATEST_TASKDEF_ARN="$(aws ecs list-task-definitions --family-prefix "${TASK_FAMILY}" --sort DESC --max-items 1 --query 'taskDefinitionArns[0]' --output text 2>/dev/null || echo "")"
[[ -n "${LATEST_TASKDEF_ARN}" && "${LATEST_TASKDEF_ARN}" != "None" ]] && export LATEST_TASKDEF_ARN && echo "LATEST_TASKDEF_ARN=${LATEST_TASKDEF_ARN}"
echo

echo "==[Resolve] Target Group health=="
if [[ -z "${TG_ARN:-}" || "${TG_ARN}" == "None" ]]; then
  TG_ARN="$(aws elbv2 describe-target-groups --query 'TargetGroups[?contains(TargetGroupName,`vendor0919-tg-new`)].TargetGroupArn|[0]' --output text 2>/dev/null || echo "")"
  export TG_ARN
fi
if [[ -n "${TG_ARN:-}" && "${TG_ARN}" != "None" ]]; then
  echo "TG_ARN=${TG_ARN}"
  aws elbv2 describe-target-health --target-group-arn "${TG_ARN}" \
    --query 'TargetHealthDescriptions[].TargetHealth.State' --output text || true
fi
echo

echo "==[Resolve] API Gateway routes/integrations=="
aws apigatewayv2 get-routes --api-id "${API_ID}" --output table || true
aws apigatewayv2 get-integrations --api-id "${API_ID}" --output table || true

APIGW_ROUTE_ID="$(aws apigatewayv2 get-routes --api-id "${API_ID}" \
  --query 'Items[?RouteKey==`$default`].RouteId|[0]' --output text 2>/dev/null || echo "")"
[[ -n "${APIGW_ROUTE_ID}" && "${APIGW_ROUTE_ID}" != "None" ]] && export APIGW_ROUTE_ID && echo "APIGW_ROUTE_ID(\$default)=${APIGW_ROUTE_ID}"

APIGW_INTEGRATION_ID="$(aws apigatewayv2 get-integrations --api-id "${API_ID}" \
  --query 'Items[0].IntegrationId' --output text 2>/dev/null || echo "")"
[[ -n "${APIGW_INTEGRATION_ID}" && "${APIGW_INTEGRATION_ID}" != "None" ]] && export APIGW_INTEGRATION_ID && echo "APIGW_INTEGRATION_ID=${APIGW_INTEGRATION_ID}"
echo

echo "==[Resolve] ECR recent images (top 5)=="
aws ecr describe-images \
  --repository-name "${ECR_REPO}" \
  --query 'reverse(sort_by(imageDetails,&imagePushedAt))[:5].[imagePushedAt, join(`,`, (imageTags || [`<none>`])) ]' \
  --output table || true
echo

echo "==[Summary]=="
echo "ECR_URI=${ECR_URI}"
echo "IMAGE_TAG_DEFAULT=${IMAGE_TAG_DEFAULT}"
echo "ALB_DNS=${ALB_DNS}"
echo "API_ID=${API_ID}  APIGW_ROUTE_ID=${APIGW_ROUTE_ID:-N/A}  APIGW_INTEGRATION_ID=${APIGW_INTEGRATION_ID:-N/A}"
echo "CLUSTER=${CLUSTER}  SERVICE=${SERVICE}  TASK_FAMILY=${TASK_FAMILY}  LATEST_TASKDEF_ARN=${LATEST_TASKDEF_ARN:-N/A}"
echo "TG_ARN=${TG_ARN:-N/A}"
EOF

chmod +x ~/bin/ttc-resolve
ttc-resolve

2) API Gateway：$defaultのみ + CORS有効（コピペOK）
2-1. ルート整理（$default 以外を削除）
# /{proxy} や /{proxy+} があれば削除
for KEY in 'ANY /{proxy}' 'ANY /{proxy+}'; do
  RID="$(aws apigatewayv2 get-routes --api-id "${API_ID}" --query "Items[?RouteKey==\`${KEY}\`].RouteId|[0]" --output text 2>/dev/null || echo "")"
  if [[ -n "${RID}" && "${RID}" != "None" ]]; then
    echo "Deleting route: ${KEY} (RouteId=${RID})"
    aws apigatewayv2 delete-route --api-id "${API_ID}" --route-id "${RID}"
  fi
done

# 結果確認（$default だけならOK）
aws apigatewayv2 get-routes --api-id "${API_ID}" --query 'Items[].{Key:RouteKey,Id:RouteId}' --output table

2-2. 統合URI（ALB直URI）を確認（必要時のみ再設定）
# 既に OK ならスキップ可
aws apigatewayv2 get-integrations --api-id "${API_ID}" \
  --query 'Items[].{Id:IntegrationId,Type:IntegrationType,Uri:IntegrationUri}' --output table


Type=HTTP_PROXY / Uri=http://vendor0919-alb-new-...elb.amazonaws.com であればOK。
update-integration は ApiGatewayManaged の都合で権限エラー表示になる場合がありますが、今は正しいURIなので不要です。

2-3. API Gateway 側 CORS を有効化（プレフライト安定）
cat > cors.json <<'EOF'
{
  "AllowOrigins": ["*"],
  "AllowMethods": ["GET","POST","OPTIONS","PUT","DELETE","PATCH","HEAD"],
  "AllowHeaders": ["*"],
  "AllowCredentials": false,
  "MaxAge": 600
}
EOF

aws apigatewayv2 update-api --api-id "${API_ID}" --cors-configuration file://cors.json
aws apigatewayv2 get-api --api-id "${API_ID}" --query '{ApiId:ApiId, Cors:CorsConfiguration}' --output json

3) FastAPI（Cursor 側・参考用）

CloudShellでは実行しません。Cursor でコードに反映。暫定は */credentials 無しでOK。

# main.py (抜粋)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/search")
def search(payload: dict):
    q = payload.get("query","")
    return {"hits":[
        {"id":"v001","title":f"Result for {q}","score":0.92,"snippet":"mock snippet 1"},
        {"id":"v002","title":f"Result for {q}","score":0.81,"snippet":"mock snippet 2"},
    ]}

4) Amplify（Cursor 側）

ビルド環境変数：
NEXT_PUBLIC_API_BASE=https://5oxz71no0m.execute-api.ap-northeast-1.amazonaws.com

フロントの fetch：

await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/search`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "omit",
  body: JSON.stringify({ query: "ping", k: 1, use_mmr: false }),
});

5) デプロイ（ECS）— ECR タグをPINして確実切替（CloudShell）
5-1. taskdef.json 生成 → 登録 → サービス更新
# 使うタグ（必要に応じて変更可）
export PIN_TAG="${IMAGE_TAG_DEFAULT}"

cat > taskdef.json <<'EOF'
{
  "family": "vendor0919-task",
  "taskRoleArn": "arn:aws:iam::067717894185:role/ecsTaskRole-vendor0919",
  "executionRoleArn": "arn:aws:iam::067717894185:role/ecsTaskExecutionRole-vendor0919",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "__ECR_URI__:__PIN_TAG__",
      "cpu": 0,
      "portMappings": [{"containerPort": 8080,"hostPort": 8080,"protocol": "tcp"}],
      "essential": true,
      "environment": [
        {"name": "VECTORSTORE_S3_BUCKET","value": "vendor-rag-0919"},
        {"name": "VECTORSTORE_LOCAL_DIR","value": "/app/vectorstore"},
        {"name": "VECTORSTORE_S3_PREFIX","value": "vectorstore/prod"}
      ],
      "secrets": [
        {"name": "DB_HOST","valueFrom": "arn:aws:secretsmanager:ap-northeast-1:067717894185:secret:vendor0919/db-credentials-DFtqRg:DB_HOST::"},
        {"name": "DB_NAME","valueFrom": "arn:aws:secretsmanager:ap-northeast-1:067717894185:secret:vendor0919/db-credentials-DFtqRg:DB_NAME::"},
        {"name": "DB_USER","valueFrom": "arn:aws:secretsmanager:ap-northeast-1:067717894185:secret:vendor0919/db-credentials-DFtqRg:DB_USER::"},
        {"name": "DB_PASSWORD","valueFrom": "arn:aws:secretsmanager:ap-northeast-1:067717894185:secret:vendor0919/db-credentials-DFtqRg:DB_PASSWORD::"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/vendor0919-api",
          "awslogs-region": "ap-northeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024"
}
EOF

sed -i "s#__ECR_URI__#${ECR_URI}#g" taskdef.json
sed -i "s#__PIN_TAG__#${PIN_TAG}#g" taskdef.json

aws ecs register-task-definition --cli-input-json file://taskdef.json
aws ecs update-service --cluster "${CLUSTER}" --service "${SERVICE}" --task-definition "${TASK_FAMILY}" --force-new-deployment

# 状態
aws ecs describe-services --cluster "${CLUSTER}" --services "${SERVICE}" \
  --query 'services[0].{TaskDef:taskDefinition,Desired:desiredCount,Running:runningCount,Pending:pendingCount}' --output table

6) 動作確認（CloudShell・毎回使えるスモーク）
ttc-resolve

APIGW_BASE="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com"

# OPTIONS (preflight)
curl -i -X OPTIONS "${APIGW_BASE}/search" \
  -H 'Origin: https://main.<AMPLIFY_HASH>.amplifyapp.com' \
  -H 'Access-Control-Request-Method: POST'

# GET /health
curl -i "${APIGW_BASE}/health"

# POST /search
curl -i -X POST "${APIGW_BASE}/search" \
  -H 'Origin: https://main.<AMPLIFY_HASH>.amplifyapp.com' \
  -H 'Content-Type: application/json' \
  -d '{"query":"ping","k":1,"use_mmr":false}'

7) 障害切り分けクイック集（CloudShell）
# APIGW のルート/統合
aws apigatewayv2 get-routes --api-id "${API_ID}" --query 'Items[].{Key:RouteKey,Target:Target}' --output table
aws apigatewayv2 get-integrations --api-id "${API_ID}" --query 'Items[].{Id:IntegrationId,Type:IntegrationType,Uri:IntegrationUri}' --output table

# ALB ターゲットの状態
aws elbv2 describe-target-health --target-group-arn "${TG_ARN}" \
  --query 'TargetHealthDescriptions[].{Id:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason}' --output table

# ECS サービス最近のイベント（デプロイ失敗/置換状況）
aws ecs describe-services --cluster "${CLUSTER}" --services "${SERVICE}" \
  --query 'services[0].events[0:10].[createdAt,message]' --output table

# アプリログ（直近10分）
aws logs filter-log-events --log-group-name "/ecs/vendor0919-api" \
  --start-time $(( ( $(date +%s) - 600 ) * 1000 )) \
  --query 'events[].message' --output text | tail -n 100

8) 最小運用メモ（要点だけ）

$defaultのみを死守（/{proxy}//{proxy+} を作らない）

統合URIはALB直固定（{proxy}を使わない）

CORSは二段構えでOK：APIGW（プレフライト安定）＋FastAPI（本応答）

フロント fetch は credentials: 'omit'（現状のCORSと整合）

デプロイは ECRタグPIN → taskdef登録 → update-service --force-new-deployment の3点セット





200になったあとに、CORSエラーが再び起きてきた件について


いま起きていたこと（超要約）

原因：ALB の片系 (ap-northeast-1c) サブネットが Public ルートテーブルに関連付いていなかったため、そのノードに当たるとタイムアウト。

対処：subnet-0fad2d28b04a7e2b5 (1c) を Public RT（IGW ルート有）に明示関連付け。以後、両 IP 宛てでも /health・/search が 200。

アプリ側：ECS タスク定義を ECR ダイジェスト固定（:22） で更新。ALB 直＆APIGW 経由ともモック JSON が返る状態を確認。

後片付け＆おすすめ設定（軽く）

CORS を最小化（必要に応じて戻す）

APIGW: AllowOrigins を Amplify の本番ドメインに限定

アプリ（FastAPI）: allow_origins も同様に限定、allow_credentials は要件に応じて

APIGW アクセスログ：すでに有効化済みなので、維持でOK（便利なのでこのまま推奨）。

監視

ALB Target Health: 1a/1c とも healthy 監視（CloudWatch アラーム化おすすめ）

APIGW 5XXError 率、ECS タスク CPU/Memory、ALB HTTPCode_ELB_5XX など

ネットワーク恒久化

ALB のサブネットは Public × 2AZ（1a/1c） 固定

その 両サブネットが IGW ルートの RT を参照していることをインフラ定義（IaC）でも明示

デプロイ運用メモ

アプリを ECR に push → 付与タグを ECR で確認

重要なリリースは @sha256 でピン留め → register-task-definition → update-service --force-new-deployment

収束待ち：aws ecs wait services-stable → 実機確認（ALB直 / APIGW）