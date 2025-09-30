# ベンダー検索システム (Next.js + FastAPI)

AIを活用したベンダー情報検索・分析プラットフォーム

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   検索UI        │  │   ブラウズUI    │  │   KBビューア  │ │
│  │  (自然言語検索)  │  │  (分類・集計)   │  │  (データ確認) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   RAG API       │  │   認証API       │  │   検索API    │ │
│  │  (ベクトル検索)  │  │  (NextAuth)     │  │  (RESTful)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   FAISS         │  │   JSON Data     │  │   OpenAI     │ │
│  │  (ベクトルDB)    │  │  (ベンダー情報)  │  │  (Embedding) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 プロジェクト構造

```
vendor0922/
├── frontend/                    # Next.js フロントエンド
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx        # ホームページ
│   │   │   ├── search/         # 検索UI
│   │   │   ├── browse/         # ブラウズUI
│   │   │   └── kb/             # ナレッジベース
│   │   └── components/ui/      # shadcn/ui コンポーネント
│   ├── package.json
│   └── env.example
├── backend/                     # FastAPI バックエンド
│   ├── main.py                 # メインAPI
│   ├── requirements.txt
│   └── env.example
├── data/                        # データファイル
│   └── vendors.json            # ベンダーデータ
├── rag_core/                    # RAG機能（既存）
│   ├── data_models.py
│   ├── loaders/
│   ├── indexer.py
│   └── vectorstore.py
├── tools/                       # ユーティリティ
│   └── reindex.py
└── Docs/                        # ドキュメント
    └── ローカル手順書.md
```

## 🚀 セットアップ

### 1. 環境準備

```bash
# リポジトリのクローン
git clone https://github.com/taksuehiro/yobi0923.git
cd yobi0923
```

### 2. バックエンド（FastAPI）のセットアップ

```bash
cd backend

# 仮想環境の作成とアクティベート
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp env.example .env
# .envファイルを編集してAPIキーを設定

# サーバー起動（本番相当）
uvicorn main:app --host 0.0.0.0 --port 8080

# 開発用（リロード有効）
uvicorn main:app --reload --port 8080
```

### 3. フロントエンド（Next.js）のセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数の設定
cp env.example .env.local
# .env.localファイルを編集

# 開発サーバー起動
npm run dev
```

## 🌐 アクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://127.0.0.1:8080
- **API仕様書**: http://127.0.0.1:8080/docs

## 🧪 テスト用コマンド

### 正常系テスト
```bash
# 検索API（正常）
curl -i -X POST http://localhost:8080/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"ping"}'

# ヘルスチェック
curl -i http://localhost:8080/health
```

### 異常系テスト
```bash
# 空ボディ → 422
curl -i -X POST http://localhost:8080/search \
  -H 'Content-Type: application/json'

# 空JSON {} → 422（min_length=1が効く）
curl -i -X POST http://localhost:8080/search \
  -H 'Content-Type: application/json' \
  -d '{}'

# デバッグ用エコー
curl -i -X POST http://localhost:8080/debug/echo \
  -H 'Content-Type: application/json' \
  -d '{"test":"data"}'
```

## 🔧 環境変数

### フロントエンド (.env.local)
```env
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8080
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### バックエンド (.env)
```env
NEXTAUTH_SECRET=dev-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VECTOR_DIR=./vectorstores/vendors_faiss
DATABASE_URL=sqlite+aiosqlite:///./backend/dev.db
ALLOWED_ORIGINS=http://localhost:3000
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## 📊 機能

### 🔍 検索機能
- 自然言語でのベンダー検索
- スコア表示とメタデータ表示
- TopK設定（1-20件）

### 📊 ブラウズ機能
- 面談ステータス別集計
- 上場区分別集計
- タイプ別集計
- クリック可能な集計カード
- マルチセレクトフィルタ

### 📚 ナレッジベース
- データ統計の表示
- メタデータ品質チェック
- 検索機能のテスト
- サンプルデータのプレビュー

## 🔄 データ管理

### ベクトルストアの再構築
```bash
# 既存のRAG機能を使用
python tools/reindex.py --input data/vendors.json --chunk_size 0
```

### データ形式
- **入力**: `data/vendors.json` (JSON形式)
- **出力**: FAISSベクトルストア
- **メタデータ**: 面談ステータス、カテゴリ、業界タグ等

## 🛠️ 開発

### API エンドポイント

#### 認証
- `POST /auth/verify` - 認証
- `GET /me` - ユーザー情報取得

#### 検索
- `POST /search` - ベンダー検索
- `GET /health` - ヘルスチェック

### フロントエンド構成
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **NextAuth.js** (認証)

### バックエンド構成
- **FastAPI**
- **Pydantic** (データ検証)
- **FAISS** (ベクトル検索)
- **LangChain** (RAG機能)

## 🚀 デプロイ

### ローカル開発
```bash
# バックエンド起動
cd backend && uvicorn main:app --reload --port 8080

# フロントエンド起動（別ターミナル）
cd frontend && npm run dev
```

### 本番環境（AWS）
- **フロントエンド**: AWS Amplify
- **バックエンド**: ECS (Fargate) + ALB
- **データ**: EFS (ベクトルストア) + S3 (原データ)

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesでお知らせください。