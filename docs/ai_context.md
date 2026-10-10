# AIコンテキスト

実装時に最初に読む要約です。画面遷移、URL、テーブル定義の正本は次のファイルです。

- 要件: `docs/requirements.md`
- 画面: `docs/screens.md`
- ルート: `docs/routes.md`
- データベース: `docs/database.md`

入力の細則で上の4つに書いていないものは `docs/coding_rules.md` に従います。作業順は `docs/tasks.md` に従います。

## アプリ

自分の PC で動かす、学習用の写真共有アプリです。友人同士が写真1枚と短いキャプションを見せ合います。公開とデプロイはしません。

- 一覧は未ログインでも見られる
- 登録とログインは、投稿する人に必要
- ログイン中の人は、いいねと、自分の投稿の削除ができる
- 投稿詳細画面は作らない。削除、いいね、ログアウトは投稿一覧から行う

## 技術

Flask、Peewee、SQLite は変更しません。パッケージの追加も、依頼があるまでしません。

| パッケージ | 役割 |
| --- | --- |
| Flask-Login | ログイン中のユーザー、`login_required` |
| Flask-Session | セッションの中身をサーバー側のファイルに保存する |
| Flask-WTF | フォームの入力チェックと CSRF |
| email-validator | メールアドレスの形式チェック |
| Pillow | 保存前に、ファイルの中身が画像かを確認する |
| python-dotenv | `.env` から `SECRET_KEY` を読む |
| Werkzeug | パスワードのハッシュ化、保存済みファイル名の確認、画像の配信 |

パスワードのハッシュ化、ファイル名の生成、画像の配信のために、これ以上のパッケージは入れません。

## ディレクトリ

コードは Blueprint に分けません。入口はプロジェクト直下の `app.py`、モデルは `models.py` です。

```text
ai_photo_share/
├── app.py
├── models.py
├── requirements.txt
├── .env
├── docs/
├── uploads/                 # 投稿画像。プロジェクト直下。Git 管理外
├── instance/
│   ├── app.db               # SQLite。Git 管理外
│   └── sessions/            # サーバー側セッション。Git 管理外
├── static/
│   └── css/
└── templates/
    ├── base.html
    ├── auth/
    │   ├── register.html
    │   └── login.html
    └── posts/
        ├── index.html
        └── new.html
```

投稿画像の保存先は、プロジェクト直下の `uploads/` です。`static/` には置きません。`static/` は CSS 用です。初期版では `static/js/` は作りません。

データベースには画像のバイト列を入れません。`posts.image_filename` には、`uploads/` へ保存したときのファイル名だけを書きます。一覧の画像は `GET /uploads/<filename>` で配信します。

## 画面とルート

テンプレートはすべて `base.html` を継承します。状態を変える処理は POST です。成功した POST はリダイレクトし、入力エラーのときは同じテンプレートを再表示します。

| 処理 | メソッドと URL | エンドポイント | テンプレート |
| --- | --- | --- | --- |
| 投稿一覧 | `GET /` | `index` | `posts/index.html` |
| ユーザー登録 | `GET, POST /register` | `register` | `auth/register.html` |
| ログイン | `GET, POST /login` | `login` | `auth/login.html` |
| ログアウト | `POST /logout` | `logout` | なし。成功後は `/` |
| 投稿作成 | `GET, POST /posts/new` | `post_new` | `posts/new.html` |
| 投稿の削除 | `POST /posts/<int:post_id>/delete` | `post_delete` | なし。成功後は `/` |
| いいねの切り替え | `POST /posts/<int:post_id>/like` | `post_like` | なし。成功後は `/` |
| 写真の表示 | `GET /uploads/<filename>` | `uploaded_file` | なし |

ナビゲーションは全画面の上部に出します。

- 常に表示: 投稿一覧
- 未ログイン: ログイン、ユーザー登録
- ログイン中: 投稿する、ログアウト

## データ

テーブルは `users`、`posts`、`likes` の3つです。定義、外部キー、ユニーク制約は `docs/database.md` に従います。

- ログインはユーザー名とパスワード。メールアドレスは登録時に必須で、ログインには使わない
- 同じユーザー名、同じメールアドレスは登録できない。英字の大文字小文字は区別しない
- キャプションは空でも投稿できる。空のときは NULL ではなく空文字
- いいね数は `posts` の列に持たない。一覧表示のときに `likes` を数える
- 1人1投稿につきいいねは1回。もう一度押すと取り消す
- 投稿を削除したら、その投稿のいいねと、`uploads/` 内の画像ファイルも削除する

## 設計資料との違い

次の2点は、要件の番号付き一覧より画面・ルート・データベースを優先します。

- ユーザー登録ではメールアドレスも必須にする
- いいねは初期版の必須機能に含める

## 作らないもの

コメント、検索、フォロー、キャプション編集、投稿詳細、ユーザー削除、ページング、メール送信、メールアドレスの本人確認、外部ストレージ、自動テスト、デプロイ。
