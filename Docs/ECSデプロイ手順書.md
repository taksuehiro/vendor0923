# AWS ECS ステージング環境デプロイ手順書

## 目的
最新のRAG実装済みbackendコードをAWS ECSステージング環境にデプロイする。

## 前提条件
- GitHubに最新コードがプッシュ済み
- AWS CLI設定済み
- ECRリポジトリ: `067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor-mock-api`
- ECSクラスター: `vendor-mock-cluster`
- ECSサービス: `vendor-mock-service`

## 手順

### 1. Docker イメージのビルド & プッシュ

```bash
# 1. ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com

# 2. イメージをビルド
cd backend
docker build -t vendor-mock-api:latest .

# 3. ECR用にタグ付け
docker tag vendor-mock-api:latest 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor-mock-api:latest

# 4. ECRにプッシュ
docker push 067717894185.dkr.ecr.ap-northeast-1.amazonaws.com/vendor-mock-api:latest
```

### 2. ECS サービスの再デプロイ

```bash
# ECSサービスを強制再デプロイ
aws ecs update-service \
  --cluster vendor-mock-cluster \
  --service vendor-mock-service \
  --force-new-deployment \
  --region ap-northeast-1
```

### 3. 稼働確認

```bash
# 1. サービス状況確認
aws ecs describe-services \
  --cluster vendor-mock-cluster \
  --services vendor-mock-service \
  --region ap-northeast-1

# 2. ヘルスチェック
curl http://vendor-mock-alb-29008868.ap-northeast-1.elb.amazonaws.com/health

# 期待されるレスポンス: {"status":"ok"}
```

### 4. 検索機能テスト

```bash
# 検索APIテスト
curl -X POST http://vendor-mock-alb-29008868.ap-northeast-1.elb.amazonaws.com/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AlphaCorpについて教えて", "top_k": 3}'
```

## 環境変数設定

### ECS タスク定義で設定が必要な環境変数:
- `OPENAI_API_KEY`: Secrets Managerから取得
- `VECTOR_DIR`: `/app/vectorstore`
- `VENDOR_DATA_JSON`: `/app/data/vendors.json`
- `ALLOWED_ORIGINS`: `http://localhost:3000,https://staging.d1234567890.amplifyapp.com`

### Amplify ステージング環境変数:
- `NEXT_PUBLIC_API_BASE`: `http://vendor-mock-alb-29008868.ap-northeast-1.elb.amazonaws.com`

## トラブルシューティング

### 1. ビルドエラー
- Dockerfileの構文確認
- requirements.txtの依存関係確認

### 2. デプロイエラー
- ECRリポジトリの存在確認
- ECSクラスター・サービスの存在確認
- IAM権限の確認

### 3. 起動エラー
- 環境変数の設定確認
- ログの確認: `aws logs describe-log-groups --log-group-name-prefix /ecs/vendor-mock`

### 4. 検索エラー
- OpenAI APIキーの設定確認
- ベクトルストアの構築確認
- CORS設定の確認

## 確認項目

- [ ] DockerイメージがECRにプッシュされた
- [ ] ECSサービスが新しいタスクで起動した
- [ ] ヘルスチェックが通る
- [ ] 検索APIがvendors.jsonのデータを返す
- [ ] AmplifyフロントエンドからAPIにアクセスできる

## 成果物

デプロイが成功し、以下の状態になること:
1. ステージング環境のフロントエンドからRAG検索機能が利用できる
2. vendors.jsonの実際のベンダーデータが検索結果として返される
3. LiberCraft/TechCorpのモックデータではなく、実際のデータが表示される




