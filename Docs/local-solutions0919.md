# 開発中に発生した問題と解決方法

## 概要
2024年9月19日の開発セッションで発生した問題点とその解決方法をまとめたドキュメントです。

---

## 1. PowerShellの構文エラー

### 問題
```bash
cd frontend && npx shadcn-ui@latest init --yes
```
実行時に以下のエラーが発生：
```
トークン '&&' は、このバージョンでは有効なステートメント区切りではありません。
```

### 原因
Windows PowerShellでは `&&` 演算子がサポートされていない（PowerShell 7以降でサポート）。

### 解決方法
コマンドを分けて実行：
```bash
cd frontend
npx shadcn-ui@latest init --yes
```

### 今後の対策
- PowerShell 7の使用を検討
- または `;` を使用（`cd frontend; npx shadcn-ui@latest init --yes`）

---

## 2. shadcn/UIのパッケージ名変更

### 問題
```bash
npx shadcn-ui@latest init --yes
```
実行時に以下の警告が表示：
```
The 'shadcn-ui' package is deprecated. Please use the 'shadcn' package instead: npx shadcn@latest init --yes
```

### 原因
`shadcn-ui` パッケージが非推奨になり、`shadcn` パッケージに統合された。

### 解決方法
```bash
npx shadcn@latest init --yes
```

### 追加の問題
ユーザーが何度も `q` でキャンセルしてしまい、プロンプトが進まない。
- 解決：`y` を入力して進めることを説明

---

## 3. Pythonの相対インポートエラー

### 問題
```python
from . import models, schemas, auth, database, security
```
実行時に以下のエラーが発生：
```
ImportError: attempted relative import with no known parent package
```

### 原因
`uvicorn main:app` で直接実行する際、相対インポートが認識されない。

### 解決方法
相対インポートを絶対インポートに変更：
```python
import models, schemas, auth, database, security
```

### 影響ファイル
- `backend/main.py`
- `backend/auth.py`

---

## 4. SQLAlchemyの非同期/同期の混在エラー

### 問題
```python
DATABASE_URL = "sqlite+aiosqlite:///./dev.db"
```
実行時に以下のエラーが発生：
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only()
```

### 原因
`aiosqlite`（非同期ドライバー）を使用しているが、同期SQLAlchemyセッションを使用している。

### 解決方法
同期SQLiteドライバーに変更：
```python
DATABASE_URL = "sqlite:///./dev.db"
```

### 追加変更
- `requirements.txt` から `aiosqlite` を削除
- `database.py` で `connect_args={"check_same_thread": False}` を追加

---

## 5. React Contextエラー（NextAuth.js）

### 問題
```typescript
// app/layout.tsx
import { SessionProvider } from "next-auth/react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
```
実行時に以下のエラーが発生：
```
React Context is unavailable in Server Components
```

### 原因
`SessionProvider` はクライアントコンポーネントだが、`layout.tsx` はServer Component。

### 解決方法
クライアントコンポーネントでラップ：
```typescript
// components/providers.tsx
"use client";
import { SessionProvider } from "next-auth/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}

// app/layout.tsx
import { Providers } from "@/components/providers";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

---

## 6. LangChainライブラリのインストール問題

### 問題
```bash
pip install langchain chromadb langchain-openai
```
実行時に以下の問題が発生：
- ChromaDBのインストールが非常に重い
- ビルド依存関係のインストールで時間がかかる
- ユーザーがキャンセルしてしまう

### 原因
- ChromaDBは大量の依存関係を持つ
- Windows環境でのビルドに時間がかかる
- 開発環境によってはインストールに失敗する可能性

### 解決方法
シンプルなテキスト検索ベースのRAGに変更：
```python
# rag_service.py
import os
import re
from typing import List, Dict, Any
from pathlib import Path

class RAGService:
    def __init__(self):
        self.documents = []
        self.docs_directory = "./docs"
    
    def _load_documents(self):
        # Markdownファイルを直接読み込み
        docs_path = Path(self.docs_directory)
        for md_file in docs_path.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.documents.append({
                    'title': md_file.stem,
                    'content': content,
                    'file_path': str(md_file)
                })
    
    def search(self, query: str, k: int = 4) -> Dict[str, Any]:
        # シンプルなキーワードマッチング
        query_lower = query.lower()
        scored_docs = []
        
        for doc in self.documents:
            score = 0
            content_lower = doc['content'].lower()
            title_lower = doc['title'].lower()
            
            if query_lower in title_lower:
                score += 10
            if query_lower in content_lower:
                score += content_lower.count(query_lower) * 2
            
            if score > 0:
                scored_docs.append({'doc': doc, 'score': score})
        
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return self._generate_answer(query, scored_docs[:k])
```

### メリット
- 軽量で高速
- 依存関係が少ない
- デバッグが容易
- 基本的な検索機能は十分

---

## 7. RAGサービスの初期化エラー

### 問題
```python
# main.py
import rag_service
rag_service.initialize()  # エラー
```
実行時に以下のエラーが発生：
```
module 'rag_service' has no attribute 'initialize'
```

### 原因
`rag_service` はモジュールだが、`initialize` メソッドはクラス内に定義されている。

### 解決方法
クラスのインスタンスを作成してから初期化：
```python
# main.py
import rag_service

try:
    rag_service_instance = rag_service.RAGService()
    rag_service_instance.initialize()
except Exception as e:
    print(f"RAG service initialization error: {e}")
    rag_service_instance = None

# 検索エンドポイントで使用
@app.post("/search")
def search_documents(request: SearchRequest):
    if rag_service_instance:
        result = rag_service_instance.search(request.query)
    else:
        result = {"answer": "RAGサービスが初期化されていません。", "sources": []}
```

---

## 8. CORSエラー

### 問題
```bash
INFO: 127.0.0.1:63354 - "OPTIONS /auth/register HTTP/1.1" 400 Bad Request
```

### 原因
- プリフライトリクエスト（OPTIONS）が適切に処理されていない
- CORS設定が不十分

### 解決方法
1. CORS設定の改善：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

2. OPTIONSハンドラーの追加：
```python
@app.options("/{path:path}")
def options_handler(path: str):
    """OPTIONSリクエストを処理"""
    return {"message": "OK"}
```

---

## 9. ディレクトリ構造の問題

### 問題
```bash
uvicorn main:app --reload --port 8000
```
プロジェクトルートから実行時に以下のエラーが発生：
```
ERROR: Error loading ASGI app. Could not import module "main".
```

### 原因
`main.py` が `backend` ディレクトリ内にあるため、プロジェクトルートからは見つからない。

### 解決方法
1. バックエンドディレクトリに移動：
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. または相対パスで実行：
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## 10. 環境変数の設定

### 問題
NextAuth.jsの設定で環境変数が未設定のエラーが発生。

### 解決方法
`.env.local` ファイルを作成：
```bash
# frontend/.env.local
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-super-secret-key
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

---

## まとめ

### 主な問題のカテゴリ
1. **環境固有の問題**: PowerShell構文、Windows環境でのビルド
2. **ライブラリの変更**: パッケージ名の変更、非推奨化
3. **設定の問題**: CORS、環境変数、ディレクトリ構造
4. **アーキテクチャの問題**: 非同期/同期の混在、Server/Client Component

### 今後の対策
1. **開発環境の統一**: Docker使用を検討
2. **依存関係の管理**: 軽量な代替手段の検討
3. **エラーハンドリング**: より詳細なエラーメッセージ
4. **ドキュメント化**: セットアップ手順の詳細化

### 学習ポイント
- 環境固有の問題は事前に確認する
- ライブラリの変更履歴をチェックする
- エラーメッセージを詳細に読む
- 段階的に問題を解決する
- 代替手段を常に検討する

---

*作成日: 2024年9月19日*
*プロジェクト: Vendor Management App (vendor0919)*
