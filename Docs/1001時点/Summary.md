プロジェクト詳細サマリー（vendor0923）
1) 背景と目的

会社AWS基盤上で Next.js(Amplify Hosting) + FastAPI(ECS/Fargate + ALB) + RAG(S3 + FAISS + Bedrock Titan Embeddings) を構築。

フロントは https 配信、API は現状 http(ALB) のため Mixed Content でブラウザからブロック。

まずは 動作検証（外部ブラウザでの検索動作確認） を安定的に行いたい。

ドメイン(本番用)が発行されたら ALB を https 化して最終接続を完成させる。

2) システム構成（現状）

Frontend: Next.js(App Router), Amplify Hosting

方針：SSG 寄せ（output: 'export' から、必要に応じ SSR/standalone にも切り替え可）

画面：/dashboard/search をメイン（検索フォーム＋結果カード）

環境変数（Amplify Console > 環境変数）：NEXT_PUBLIC_API_BASE で API ベースURLを指定

Backend: FastAPI(Uvicorn) on ECS/Fargate, ALB 経由

ヘルスチェック：HTTP :8080/health（200）

エンドポイント：/search（S3上のFAISS + Bedrock 埋め込みで検索）

RAG ストレージ: S3 vendor-rag-0919/vectorstores/*（FAISS データ）

Embedding: Bedrock Titan（amazon.titan-embed-text-v2:0）

IAM（タスクロール）: ecsTaskRole-vendor0919

Vendor0919S3AccessPolicy（S3 読み取り）

Vendor0919BedrockInvokePolicy（Bedrock Invoke）

3) 最近の出来事・対応履歴（要点）

ModuleNotFoundError: langchain_aws → langchain_community に切り替え、解消。

ECS タスクが ALB ヘルスチェックで落下 → TaskDef:68 へ更新後、安定。

/search で S3 403 → S3 ポリシーを vectorstores/* に拡張し解消。

フロントは UI を 旧UI（ALB直叩き）へロールバックし、検索画面を整備。

ALB ヘルス：healthy、/health は 200、/search は curl で JSON 返却まで確認済み。

ブラウザからは Mixed Content によりブロック（https→http）→ ドメイン到着後に https 完全化で解消する方針に合意。

4) 現在の状態（チェック）

ALB: vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com

TG ヘルス: healthy（describe-target-health 済）

API 動作（curl 例）

BASE="http://vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com"
curl -i "$BASE/health"             # ← 200 OK
curl -s -X POST "$BASE/search" \
  -H 'content-type: application/json' \
  -d '{"query":"テスト","k":4,"use_mmr":true}' | jq   # ← JSONのhits/resultsが返る


ログ（CloudWatch）：/ecs/vendor-app に GET /health 200 が周期的に記録、異常なし。

IAM：S3/Bedrock の必要権限を確認済（JSON取得でプレフィックスも正しい）。

5) 暫定運用（本番 https 完成まで）

「自分のブラウザで動けばOK」の要件を満たす選択肢

最も安全：ローカル開発（Cursor/Next.js dev）で http→http 接続

frontend/.env.local

NEXT_PUBLIC_API_BASE=http://vendor0919-alb-new-619968933.ap-northeast-1.elb.amazonaws.com


npm run dev → http://localhost:3000 から検索実行（Mixed Content なし）

（非推奨の検証専用）：Chrome を --allow-running-insecure-content で起動

https(Amplify)→http(ALB) を強制許可。短期検証のみ。

※ CloudFront で ALB をラップして暫定 https 化も可能だが、今回は「ドメイン待ち」で見送り。

6) ドメイン到着後の本番対応（Runbook）
6.1 設計

DNS 管理（Route53）が 個人アカウントでも、会社アカウントの ALB に CNAME で向ければOK。

ただし ACM 証明書は ALB と同じアカウント＆同じリージョン（東京）で発行必須。

DNS 検証の CNAME は 個人アカウントの Route53 に登録すれば検証完了できる（クロスアカウント検証）。

6.2 手順（会社アカウントで実施）

ACM 証明書の発行（東京）

対象：api.<your-domain>（サブドメイン推奨）

検証：DNS（CNAME）

→ ACM が提示する CNAME を DNS管理側(Route53) に登録（個人アカウントの場合は手動で登録）

ALB に HTTPS(443) リスナー追加

LB_ARN=<ALB ARN>
TG_ARN=<TG ARN>
CERT_ARN=<ACM 証明書ARN>

aws elbv2 create-listener \
  --region ap-northeast-1 \
  --load-balancer-arn $LB_ARN \
  --protocol HTTPS --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN

# 任意：80→443 リダイレクト
aws elbv2 modify-listener \
  --region ap-northeast-1 \
  --listener-arn $(aws elbv2 describe-listeners --region ap-northeast-1 --load-balancer-arn $LB_ARN --query 'Listeners[?Port==`80`].ListenerArn' --output text) \
  --default-actions 'Type=redirect,RedirectConfig={Protocol=HTTPS,Port="443",StatusCode=HTTP_301}'


DNS（Route53）で CNAME 設定（DNSが個人アカウントでもOK）

api.<your-domain>  CNAME  <ALBのDNS名>


伝播後、https://api.<your-domain>/health が 200 になることを確認。

Amplify の環境変数更新

NEXT_PUBLIC_API_BASE=https://api.<your-domain>


→ 再デプロイ（Build が SSR/standalone の場合は amplify.yml のアーティファクトパスも確認）

ブラウザで動作確認

Network: https://api.<your-domain>/search が 200/JSON

Mixed Content が消えていることを確認

7) クロスアカウントでの注意

DNS(個人) ↔ ACM/ALB(会社) は問題なし（CNAME で疎通、ACM の DNS 検証も可能）。

ただし将来、本番ドメインへ切替時は 新しい証明書を会社アカウントで発行 → ALB へ差し替え → Amplify の環境変数更新 を再度行う。

セキュリティ観点：一時的に個人ドメインを使う旨は関係者に合意を取る。

8) 運用 Runbook（よく使う確認コマンド）
8.1 ECS/ALB
# ターゲットヘルス
TG_ARN=$(aws elbv2 describe-target-groups --names vendor0919-tg-new --region ap-northeast-1 --query 'TargetGroups[0].TargetGroupArn' --output text)
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region ap-northeast-1

# サービス再起動（権限更新やイメージ更新後）
aws ecs update-service --region ap-northeast-1 --cluster vendor0919-cluster --service vendor0919-service --force-new-deployment

# ログ追尾（実際のロググループに置換）
aws logs tail /ecs/vendor-app --since 15m --follow --region ap-northeast-1

8.2 API 疎通
BASE="https://api.<your-domain>"  # 暫定は http://<ALB DNS>
curl -i "$BASE/health"
curl -s -X POST "$BASE/search" -H 'content-type: application/json' -d '{"query":"テスト","k":4,"use_mmr":true}' | jq

8.3 IAM（参考：中身を確認）
ROLE_NAME=ecsTaskRole-vendor0919
S3POLICY_ARN=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyName=='Vendor0919S3AccessPolicy'].PolicyArn" --output text)
BEDROCKPOLICY_ARN=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyName=='Vendor0919BedrockInvokePolicy'].PolicyArn" --output text)

S3_VER=$(aws iam list-policy-versions --policy-arn "$S3POLICY_ARN" --query 'Versions[?IsDefaultVersion].VersionId' --output text)
aws iam get-policy-version --policy-arn "$S3POLICY_ARN" --version-id "$S3_VER" --query 'PolicyVersion.Document' --output json

BR_VER=$(aws iam list-policy-versions --policy-arn "$BEDROCKPOLICY_ARN" --query 'Versions[?IsDefaultVersion].VersionId' --output text)
aws iam get-policy-version --policy-arn "$BEDROCKPOLICY_ARN" --version-id "$BR_VER" --query 'PolicyVersion.Document' --output json

9) 既知の落とし穴と対処

Mixed Content：Amplify(https) → API(http) は拒否。ALB を https 化するか、ローカル(http)で確認。

S3 403：ポリシーのパス誤り（vectorstore/* vs vectorstores/*）。正しくは vectorstores/*。

Health UNKNOWN：タスクは RUNNING でも ALB Healthy 未登録だと応答が来ない。少し待つ or ログ確認。

依存エラー：langchain_aws → langchain_community を使用する（再発注意）。

証明書の場所：ACM は ALB と同じアカウント・同リージョンで発行が必要。Route53 は別アカウントでもOK（DNS検証CNAME登録）。

10) 残タスク（ToDo）

 独自ドメイン取得（暫定 or 本番）

 会社アカウントで ACM 証明書発行（DNS 検証は個人Route53でも可）

 ALB に HTTPS(443) リスナー追加、80→443 リダイレクト（任意）

 Amplify の NEXT_PUBLIC_API_BASE を https://api.<your-domain> に更新

 Amplify 再デプロイ → ブラウザで /search が 200/JSON を返すことを確認

 （任意）CloudFront or WAF、セキュリティヘッダなど強化