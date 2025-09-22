Amplify フロントエンド構築での試行錯誤まとめ
1. モノレポ構成での設定
問題点

frontend/ にアプリがあるモノレポ構成

AMPLIFY_MONOREPO_APP_ROOT=frontend を環境変数に入れたら

CustomerError: Monorepo spec provided without "applications" key


とエラー発生

解決策

選択肢①: amplify.yml を Gen1 フォーマット（applications: ～ appRoot: frontend）に修正

選択肢②: 環境変数から AMPLIFY_MONOREPO_APP_ROOT を削除 → シンプルな Gen2 フォーマットでOK
👉 今回は②で対応、frontend専用として進めた。

2. ESLint によるビルド失敗
問題点

Amplify は next build 実行時に ESLint も走る

ローカルでは Warning だった any 使用などが Error 扱い となりビルド失敗

解決策

package.json の build スクリプトを修正

"build": "next build --no-lint"


Lint をビルドから外すことで通過
👉 後でローカルで Lint を直す方針に変更。

3. TypeScript の strict check エラー
問題点

catch (error) で error が unknown 型になり、.message にアクセスできず失敗

dashboard や search ページで複数発生

解決策

catch を以下のように修正

} catch (error: unknown) {
  if (error instanceof Error) {
    setApiResponse({ error: error.message });
  } else {
    setApiResponse({ error: String(error) });
  }
}


👉 全ての catch に型安全なハンドリングを追加。

4. NextAuth セッション型のエラー
問題点

session.user.id が存在しない扱いでエラー

session.accessToken に unknown を代入しようとしてエラー

解決策

一時対応: 型アサーションで回避

(session.user as any).id = token.id as string;
(session as any).accessToken = token.accessToken as string;


長期的対応: types/next-auth.d.ts を作成し、Session 型を拡張する

declare module "next-auth" {
  interface Session {
    user?: {
      id?: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
    accessToken?: string;
  }
}


5. vendor0913 との比較による解決
問題点

vendor0919 ではモノレポ設定の扱いでエラーが続発し、`CustomerError: Monorepo spec provided without "applications" key` などが発生。
一方、ほぼ同じ構成の vendor0913 は正常動作していたため、設定差分を比較することにした。

解決策

vendor0913 の amplify.yml を確認し、以下の違いを発見：
- `applications:` ブロックを使用し、モノレポとして正しく宣言している
- Node.js バージョンを明示的に `nvm install 20 && nvm use 20` で指定している
- キャッシュに `.next/cache` を含めている

vendor0919 の amplify.yml を vendor0913 と同じ形式に修正：

```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - nvm install 20
            - nvm use 20
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: .next
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
          - .next/cache/**/*
結果

この修正により、vendor0919 も vendor0913 と同様にビルド成功。
モノレポ環境では「applications: ～ appRoot: frontend」形式に統一するのが安定と分かった。




✅ 最終的な学び

AmplifyはLintやTypeチェックが本番レベルで厳しい → ローカルでWarningでもAmplifyでは落ちる

モノレポはシンプル構成で進める方が楽（frontend専用でOK）

型拡張はNextAuthの必須作業 → 最初から next-auth.d.ts を入れておくとスムーズ

短期的には as any、長期的には型拡張 という二段構えが現実的