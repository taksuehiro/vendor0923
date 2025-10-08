個人アカウント（ドメイン管理側）

ドメイン登録: 3ii.biz を Route53 の Registered domains で取得済み

Hosted Zone: 3ii.biz の Hosted Zone を保有

ACM検証CNAME: 会社ACMが提示する CNAME を 個人のHosted Zone に作成 → 証明書が “発行済み”

API向けのDNS:

api.3ii.biz の CNAME を作成

値: vendor0919-alb-new-xxxx.ap-northeast-1.elb.amazonaws.com（会社ALBのDNS名）

※クロスアカウントのため Alias(A)は使えずCNAMEを使用（UIに会社ALBは出てこないため）

会社アカウント（アプリ/ネットワーク側）

ACM(東京リージョン): api.3ii.biz で発行（検証は個人Route53のCNAMEで実施）

ALB:

443/HTTPS リスナーに上記ACM証明書をアタッチ

80/HTTP → 443/HTTPS へ リダイレクト(HTTP_301) を設定済み

セキュリティグループ: ALBに 0.0.0.0/0 TCP 443 を許可

ターゲットグループ: バックエンド(例 10.0.2.151:8080) が healthy

ECS(FastAPI): /health(GET), /search(POST) を提供

S3（RAGデータ）:

バケット: vendor-rag-0919

パス: vectorstore/prod/index.faiss と index.pkl（本命）、vectorstores/prod/...（ミニ版）

起動時に S3 → /tmp にDL → FAISSロードする実装に収束

Route53 が重要な理由とポイント（個人×会社のクロス構成）

ACMドメイン検証CNAMEは “ドメインを持っている側”（= 個人Hosted Zone）に作成する
→ 会社アカウントのACMでも、検証レコードは個人Hosted Zone でOK

API用DNS(api.3ii.biz) は “どこに向けるか” を決めるのは 個人のHosted Zone

会社ALBは別アカウントなので、Alias(A)のUI選択に登場しない

よって CNAME で ALB の DNS 名（*.elb.amazonaws.com）を 手動入力するのが正解

ルートドメイン（3ii.biz）は CNAME 不可だが、サブドメイン（api.3ii.biz）ならCNAME可（今回のケースは問題なし）

検証コマンド・ログ（事実ベース）

ターゲット正常性

aws elbv2 describe-target-health --target-group-arn <TG_ARN>
# healthy 確認


ALB リスナー

aws elbv2 modify-listener --listener-arn <80のARN> \
  --default-actions Type=redirect,RedirectConfig='{Protocol="HTTPS",Port="443",StatusCode="HTTP_301"}'


Route53 記録一覧（会社側はHosted Zoneなし/個人側にあり）

aws route53 list-hosted-zones
aws route53 list-resource-record-sets --hosted-zone-id <個人HostedZoneID> \
  --query "ResourceRecordSets[?Name == 'api.3ii.biz.']"


疎通確認

curl -I https://api.3ii.biz/health → 405(HEAD) / allow: GET（仕様どおり）

curl https://api.3ii.biz/health → 200 OK

curl -X POST https://api.3ii.biz/search -d '{"query":"…"}' → 200 + JSON

CloudWatch Logs（ECS）

/ecs/vendor0919-api で GET /health 200 多数、/ は 404

aws logs tail /ecs/vendor0919-api --follow で追跡

ALB アクセスログ（S3）

S3: vendor0919-alb-logs/... .log.gz をダウンロード・展開して /search を grep

直近ファイルで /search が出ない場合は別時間帯のログも併せて要確認