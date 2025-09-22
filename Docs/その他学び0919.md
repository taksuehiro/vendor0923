# vendor0919 ECS + Aurora 構築作業記録

## Day XX: ECSタスクからAurora疎通まで

### 1. タスクIDの取得
```bash
aws ecs list-tasks --cluster vendor0919-cluster --region ap-northeast-1
# → a0cd2c35ccf54e919ee289f8e0431a39
2. コンテナ名の取得
bash
コードをコピーする
aws ecs describe-tasks \
  --cluster vendor0919-cluster \
  --tasks a0cd2c35ccf54e919ee289f8e0431a39 \
  --region ap-northeast-1 \
  --query "tasks[0].containers[0].name" \
  --output text
# → api
3. ECS Exec でタスクに入る
bash
コードをコピーする
aws ecs execute-command \
  --cluster vendor0919-cluster \
  --task a0cd2c35ccf54e919ee289f8e0431a39 \
  --container api \
  --interactive \
  --command "/bin/sh"
4. ネットワーク疎通確認
bash
コードをコピーする
python - <<'PY'
import socket
host="vendor0919-aurora-instance-1.czicicu6kcc8.ap-northeast-1.rds.amazonaws.com"
port=5432
s=socket.socket(); s.settimeout(5)
try:
    s.connect((host, port))
    print("TCP:OK")
except Exception as e:
    print("TCP:NG", e)
finally:
    s.close()
PY
# → TCP:OK
✅ 試行錯誤ポイント: ここで timeout が出なければネットワークは通ってる。

5. psql クライアントのインストール
bash
コードをコピーする
apt-get update && apt-get install -y postgresql-client
6. Aurora へ SELECT 1
bash
コードをコピーする
export DB_HOST="vendor0919-aurora-instance-1.czicicu6kcc8.ap-northeast-1.rds.amazonaws.com"
export DB_NAME="postgres"
export DB_USER="masteruser"
export DB_PASSWORD="YourStrongPassw0rd!"

psql "host=$DB_HOST port=5432 dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD" -c "SELECT 1;"
# → 1 が返って成功
Day XX: Secrets Manager 化
7. Secrets Manager に登録
bash
コードをコピーする
aws secretsmanager create-secret \
  --name vendor0919/db-credentials \
  --description "Aurora credentials for vendor0919 ECS service" \
  --secret-string '{
    "DB_HOST": "vendor0919-aurora-instance-1.czicicu6kcc8.ap-northeast-1.rds.amazonaws.com",
    "DB_NAME": "postgres",
    "DB_USER": "masteruser",
    "DB_PASSWORD": "YourStrongPassw0rd!"
  }' \
  --region ap-northeast-1
# → ARN が返る
8. タスク実行ロールに権限付与
bash
コードをコピーする
aws iam attach-role-policy \
  --role-name ecsTaskRole-vendor0919 \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
9. タスク定義 JSON を作成
bash
コードをコピーする
cat << 'EOF' > vendor0919-task-def.json
{
  "family": "vendor0919-task",
  "executionRoleArn": "arn:aws:iam::067717894185:role/ecsTaskExecutionRole-vendor0919",
  "taskRoleArn": "arn:aws:iam::067717894185:role/ecsTaskRole-vendor0919",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "secrets": [
        {
          "name": "DB_HOST",
          "valueFrom": "<ARN>:DB_HOST::"
        },
        {
          "name": "DB_NAME",
          "valueFrom": "<ARN>:DB_NAME::"
        },
        {
          "name": "DB_USER",
          "valueFrom": "<ARN>:DB_USER::"
        },
        {
          "name": "DB_PASSWORD",
          "valueFrom": "<ARN>:DB_PASSWORD::"
        }
      ]
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024"
}
EOF
10. 新タスク定義を登録
bash
コードをコピーする
aws ecs register-task-definition \
  --cli-input-json file://vendor0919-task-def.json \
  --region ap-northeast-1
11. サービス更新で再デプロイ
bash
コードをコピーする
aws ecs update-service \
  --cluster vendor0919-cluster \
  --service vendor0919-service \
  --task-definition vendor0919-task:5 \
  --force-new-deployment \
  --region ap-northeast-1
Day XX: アプリ修正 /db-check 実装
12. FastAPI に /db-check を追加
bash
コードをコピーする
cat << 'EOF' > backend/main.py
from fastapi import FastAPI
import os, psycopg2

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def db_check():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            connect_timeout=5
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            result = cur.fetchone()
        conn.close()
        return {"status": "ok", "message": "DB connection successful", "result": result}
    except Exception as e:
        return {"status": "ng", "error": str(e)}
EOF
13. Dockerビルド & ECR Push
bash
コードをコピーする
docker build -t vendor0919-api:latest backend/
docker tag vendor0919-api:latest 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest
docker push 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor0919-api:latest
14. ECS再デプロイ
bash
コードをコピーする
aws ecs update-service \
  --cluster vendor0919-cluster \
  --service vendor0919-service \
  --force-new-deployment \
  --region ap-northeast-1
最終確認
bash
コードをコピーする
curl http://vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com/health
# → {"status":"ok"}

curl http://vendor0919-alb-1049264719.ap-northeast-1.elb.amazonaws.com/db-check
# → {"status":"ok","message":"DB connection successful","result":[1]}
✅ 完成: ALB経由でAuroraに接続できる「最低限動くアプリ」稼働

試行錯誤ポイントまとめ
最初 psql が無くて疎通確認できず → コンテナに postgresql-client を追加して解決

aws secretsmanager をタスク内で実行して aws: not found → ローカルで実行し直し

タスク定義ファイル vendor0919-task-def.json が無い → cat << 'EOF' で作成して登録

/db-check をシェルに直接打ち込んでしまい bash エラー → FastAPIコードに追記して再デプロイ