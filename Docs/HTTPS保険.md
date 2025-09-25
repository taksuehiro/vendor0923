うん、①（API Gateway で ALB を HTTPS ラップ）のまま進めても、**本番で証明書(ACM)が出たら“元に戻す”（= 直で ALB/独自ドメインの HTTPS を使う）**のはカンタンです。
実際の切替は「フロントの API_BASE を差し替えるだけ」で完了します。API Gateway はしばらく残しておけば即ロールバックも可能です。

安全に“元に戻す”手順（コピペ運用）

前提：env.sh に下記を追記（足りない分）

# 追加（ALB/ACM向け）
export ALB_ARN=arn:aws:elasticloadbalancing:ap-northeast-1:XXXXXXXXXXXX:loadbalancer/app/vendor0919-alb-new/XXXXXXXXXXXXXXX
export ACM_CERT_ARN=arn:aws:acm:ap-northeast-1:XXXXXXXXXXXX:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# 既にあるはず:
# REGION, TG_ARN, ALB_SG, ALB_DNS など

1) ALB を HTTPS(443) 対応させる
# scripts/07_enable_alb_https.sh
#!/usr/bin/env bash
set -euo pipefail
source ./env.sh

# 443 を SG に開ける（既に開いていれば自動で失敗→無視）
aws ec2 authorize-security-group-ingress \
  --group-id "$ALB_SG" \
  --ip-permissions IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges='[{CidrIp=0.0.0.0/0,Description="HTTPS"}]' \
  --region "$REGION" 2>/dev/null || true

# 既存リスナーを確認（80 番）
LIST80=$(aws elbv2 describe-listeners --load-balancer-arn "$ALB_ARN" --region "$REGION" \
  --query 'Listeners[?Port==`80`].ListenerArn' --output text)

# 443 リスナーが無ければ作成
HAS443=$(aws elbv2 describe-listeners --load-balancer-arn "$ALB_ARN" --region "$REGION" \
  --query 'Listeners[?Port==`443`].ListenerArn' --output text || true)
if [ -z "$HAS443" ]; then
  aws elbv2 create-listener \
    --load-balancer-arn "$ALB_ARN" \
    --protocol HTTPS --port 443 \
    --certificates CertificateArn="$ACM_CERT_ARN" \
    --ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06 \
    --default-actions Type=forward,TargetGroupArn="$TG_ARN" \
    --region "$REGION" >/dev/null
  echo "✅ ALB HTTPS(443) listener 作成"
else
  echo "ℹ️ 443 リスナーは既に存在"
fi

# （任意）80→443 リダイレクトに変える
if [ -n "$LIST80" ]; then
  aws elbv2 modify-listener \
    --listener-arn "$LIST80" \
    --default-actions Type=redirect,"RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
    --region "$REGION" >/dev/null || true
  echo "✅ 80→443 リダイレクト設定"
fi

echo "🔎 動作チェック: curl -k https://$ALB_DNS/health"


実行:

bash scripts/07_enable_alb_https.sh


ポイント

**ACM は ALB と同じリージョン（ap-northeast-1）**の証明書を使います。

まずは ALB の https://<ALB_DNS> で動く状態にします（独自ドメイン未申請でもOK）。

2) フロントのエンドポイントを差し替える（ゼロダウンタイム）

Amplify(フロント)の .env（またはビルド時環境変数）を、
API_BASE=https://<ALB_DNS> に変更 → 再デプロイ。

CORS の設定は不要（同一オリジンではないが、バックエンドが ALB 直で HTTPS なら混在コンテンツの問題は消えます）。
※ バックエンド側が CORS 許可する API の場合は従来通り Access-Control-Allow-Origin を忘れずに。

ロールバックは .env の API_BASE を API Gateway の HTTPS エンドポイントに戻すだけ。

3) （独自ドメインが取れたら）DNS を切替

A/AAAA レコードを ALB の DNS もしくは CloudFront に向けるだけ。

既に ALB 443 が生きていれば、DNS TTL 分の伝播待ちで切替完了。

4) 片付け（不要になったら）
# scripts/08_cleanup_apigw.sh
#!/usr/bin/env bash
set -euo pipefail
# API_ID をメモしてある前提。忘れた場合は list-apis で探す。
API_ID="$1"
aws apigatewayv2 delete-api --api-id "$API_ID" --region ap-northeast-1
echo "🧹 API Gateway ($API_ID) を削除しました"

よくある質問（要点）

Q. 切り戻しは速い？
A. はい。Amplify の環境変数を戻して再デプロイするだけ。API Gateway 自体は残しておけば即復旧可能です。

Q. CloudFront を間に挟む必要ある？
A. 必須ではありません（ALB の *.elb.amazonaws.com を HTTPS で直叩き可能）。将来 WAF/キャッシュを入れたいときに CloudFront を追加検討でOK。

Q. 本番の HTTPS は ALB と API Gateway のどっち？
A. どちらでも可ですが、ECS/ALB 構成なら ALB 443 が素直。API Gateway はスロットリング/CORS/認証を楽したい時に便利。

まとめ

①方式で進めてOK。本番の証明書が出たら上記スクリプトで ALB を 443 化 → フロントの API_BASE を差し替えるだけ。

問題が出たら .env を API Gateway に戻して即ロールバックできます。

必要なら、あなたの環境値（ALB_ARN/ACM_CERT_ARN）が埋まった状態のスクリプトをこちらで作り込みます。