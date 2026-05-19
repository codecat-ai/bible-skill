[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)

# Bible Skill

Bible Skill は、決定的な聖書箇所検索のための MIT ライセンスの Python CLI と再利用可能な AI Agent スキルです。モデルの記憶に頼るのではなく、ダウンロード済み翻訳データと厳密なローカル参照解析を使うことで、Agent が不正確な聖句引用や幻覚的な引用箇所を避けられるようにします。

このパッケージはまだパッケージレジストリに公開されていません。ソースチェックアウトからのみ使用してください。

## 課題と動機

LLM は聖書箇所を大まかには知っていますが、翻訳を混ぜたり、語句を落としたり、範囲を誤ったり、存在しない文言を生成したりすることがあります。Bible Skill は、翻訳の発見、許可された翻訳のダウンロード、ローカルデータの一覧表示、指定された書・章・節・範囲の正確な検索という、Agent 向けの再現可能なワークフローを提供します。

## 機能

- Free Use Bible API から利用可能な翻訳を発見します。
- 完全な翻訳をローカルデータディレクトリにダウンロードします。
- インストール済み翻訳を、書・章・節の数とともに一覧表示します。
- インストール済み翻訳キャッシュファイルの必須メタデータ、書/章/節構造、空でない節本文、決定的なチェックサムを検証します。
- 転送自動化向けに、翻訳メタデータ、POSIX 形式の相対パス、チェックサム、件数、検証問題を含むポータブルなキャッシュマニフェストを検査します。
- ID、名前、言語、ライセンス URL、ソース URL でインストール済み翻訳のメタデータをローカル検索します。
- 書、章、単節、節範囲、同一書内の章をまたぐ範囲でローカル箇所を検索します。
- 同じローカル解析器と書データを使って、任意のノート、説教原稿、Markdown から聖書参照を抽出します。
- ローカル検索結果をノート向け Markdown または最小で決定的な USFM 風テキストとして出力し、任意でローカル翻訳の帰属情報も含められます。
- 2 つ以上のインストール済み翻訳で同じローカル箇所をテキスト、JSON、Markdown、または CSV で比較します。
- 翻訳全体をダウンロードせずに正確な箇所を調べるため、bible-api.com をライブフォールバックとして使え、テキスト、生 JSON、Markdown、CSV で出力でき、タイムアウト/リトライ設定も構成できます。
- ライブプロバイダーの HTTP 失敗では、有用なプロバイダーメッセージ、短い本文抜粋、利用可能な `Retry-After` の待機ヒントを表示します。
- AI Agent ワークフロー向けに Hermes 互換の `SKILL.md` を出力します。

## インストール

ソースリポジトリをクローンします：

```sh
git clone https://github.com/codecat-ai/bible-skill.git
cd bible-skill
python -m bible_skill.cli --help
```

チェックアウト内でローカルのコマンドエントリポイントを試す場合は、自分の仮想環境でこのチェックアウトを編集可能モードでインストールします：

```sh
python -m venv .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
bible-skill --help
```

`pip install bible-skill`、`uvx bible-skill`、または同様のレジストリ用コマンドは使わないでください。レジストリ公開版はまだありません。

## オフライン/ローカル専用 Agent セットアップ

オフラインまたはローカル専用の Agent 作業では、信頼できるソースチェックアウトを使います。ネットワーク使用が許可されている間に、利用可能なローカル翻訳データを準備または更新し、そのデータを検証してから Agent に渡します：

```sh
git clone https://github.com/codecat-ai/bible-skill.git
cd bible-skill
python -m venv .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill validate --data-dir ./data
bible-skill cache manifest --data-dir ./data --json
bible-skill installed --data-dir ./data
bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md
```

生成した `skills/bible-skill/SKILL.md` を Agent に指定します。ローカル検索コマンドでは同じ `--data-dir ./data` を使い続けてください。インストール済み翻訳を優先し、返された本文、正規化済み参照、翻訳 ID、帰属メタデータを保持します。タスクが明示的にネットワーク使用を許可しない限り、ライブフォールバックを無効にします。

## クイックスタート

```sh
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill installed --data-dir ./data
bible-skill validate --data-dir ./data
bible-skill validate web --data-dir ./data --json
bible-skill cache manifest --data-dir ./data --json
bible-skill search english --data-dir ./data
bible-skill search license.example --data-dir ./data --json
bible-skill query web "John 3:16" --data-dir ./data
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --json
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --markdown
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --markdown --attribution
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --usfm
bible-skill compare "John 3:16" web kjv --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --markdown
bible-skill compare "John 3:16" web kjv --data-dir ./data --csv
bible-skill compare "John 3:16" web kjv --data-dir ./data --csv --attribution
bible-skill extract --text "Discuss John 3:16 and Romans 8:28-30."
bible-skill extract --text "Discuss John 3:16 and Romans 8:28-30." --markdown
bible-skill extract --file sermon-notes.md --json
bible-skill extract --file sermon-notes.md --markdown
bible-skill extract --file sermon-notes.md --csv
bible-skill live "John 3:16" --translation web
bible-skill live "John 3:16" --translation web --timeout 10 --retries 2
bible-skill live "John 3:16" --translation web --markdown
bible-skill live "John 3:16" --translation web --csv
bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md
```

## 参照精度

ローカル検索は次を受け付けます：

- 書全体：`John`
- 章：`John 3`
- 単節：`John 3:16`
- 同一章の範囲：`John 3:16-18`
- 同一書内の章をまたぐ範囲：`John 3:16-4:2`
- USFM 書 ID：`JHN 3:16`

## 参照抽出

箇所検索や比較の前に、`bible-skill extract` でノート、説教原稿、Markdown をスキャンできます。`--text TEXT` と `--file PATH` は同時に指定できず、どちらか一方が必須です。テキスト出力では、最初に現れた順序を保ちながら、重複を除いた正規化済み参照を 1 行に 1 件ずつ出力します。`--json` は、マッチした文字列、正規化済み参照、文字オフセット、書 ID/名前、開始/終了の章と節を含む行を出力します。`--markdown` は `# Extracted Bible references` で始まる、ノートに貼り付けやすい要約を出力します。マッチがある場合は、太字の正規化済み参照とエスケープ済みの元コンテキストを各行に出し、ない場合は `No Bible references found.` を出力します。`--csv` は `reference`、`book`、`chapter`、`start_verse`、`end_verse`、`start`、`end`、`context` 列を持つ表計算向けの行を出力し、マッチがない場合もヘッダー行だけを出力します。`--json`、`--markdown`、`--csv` は同時に指定できません。

純粋な Python API として `bible_skill.extract.extract_references(text)` も利用でき、Agent やアプリケーションのワークフローに組み込めます。抽出は `parse_reference` と同じ書名、別名、USFM ID を認識し、`John 3:16`、`JHN 3:16-4:2`、`Genesis 1`、`Romans 8:28-30` などの形式に対応します。

## 設定

`--data-dir` でダウンロード済み翻訳の保存先を指定します。指定しない場合、Bible Skill はプラットフォームに合ったユーザーデータディレクトリを使います。ダウンロード記録には、翻訳メタデータ、ソース URL、取得時刻、提供元が返すライセンス URL、そして正規化済み翻訳内容から計算した決定的な `sha256:` チェックサムが含まれます。取得時刻はチェックサムに含めません。`validate` コマンドは、Agent がキャッシュに依存する前にインストール済みキャッシュファイルを検査します。任意の翻訳 ID を指定するとそのキャッシュだけを検証し、ID を省略するとすべてのインストール済み翻訳を検証します。テキスト出力は簡潔なタブ区切りで、`--json` は `translation_id`、`ok`、`checksum`、`issues` を含むオブジェクトを出力します。要求されたキャッシュのいずれかが存在しない、または無効な場合、検証は非ゼロで終了します。

ローカルキャッシュを別のマシンや Agent ワークスペースへ移す前に、`bible-skill cache manifest --data-dir ./data --json` を実行できます。このマニフェストは検査用の補助情報であり、パッケージやレジストリの主張ではありません。`schema_version`、`generated_at`、`data_dir` に加えて、各キャッシュディレクトリの id、名前、言語、ライセンス/ソース URL、書/章/節の数、チェックサム、POSIX 形式の `relative_path`、`validation_ok`、`issues` を出力します。自動化ではデータディレクトリをコピーし、転送前後のマニフェストを比較してから、転送先で `bible-skill validate --data-dir ./data` を実行できます。欠落または破損したキャッシュファイルは、可能な限りマニフェスト全体を失敗させずに問題リストとして表現されます。`search` と `compare` コマンドはインストール済みのローカル翻訳だけを読むため、ローカルメタデータ検索や比較を行う各翻訳を先にダウンロードしてください。

ローカル `query` は既定でテキストを出力し、`--json` では機械可読な箇所オブジェクト、`--markdown` では正規化済み参照と翻訳 ID を見出しにしたノート向け Markdown、`--usfm` では最小で決定的な USFM 風テキストを出力します。`--json`、`--markdown`、`--usfm` は同時に指定できません。ローカル `query` または `compare` の出力に `--attribution` を渡すと、利用可能な `license_url` と `source_url` メタデータを含めます。JSON は要求された場合だけ構造化された `attribution` オブジェクトを追加し、compare CSV は安定した `license_url` と `source_url` 列を追加します。

ライブフォールバックでは、`--json` でプロバイダーの生レスポンスを出力でき、`--markdown` でノートに貼り付けやすい形式を出力でき、`--csv` で `reference`、`translation`、`verse_reference`、`text` 列を持つ表計算向けの行を出力できます。`--json`、`--markdown`、`--csv` は同時に指定できません。`--timeout SECONDS` で既定の 30 秒からプロバイダーリクエストのタイムアウトを変更でき、`--retries COUNT` で一時的なネットワークエラーや 408、429、5xx などの一時的な HTTP レスポンスを再試行できます。既定のリトライ回数は 0 のため、明示的に指定しない限り従来どおり 1 回だけ試行します。404/no passage found のような意味的なプロバイダー応答は再試行しません。Markdown と CSV のレンダリングは bible-api.com 形状のペイロードとの互換性を保ち、トップレベルの `data` オブジェクトで包まれたプロバイダーペイロード、`verses` または `passages` という名前の節リスト、`text`、`content`、`verse_text`、またはネストした配列/オブジェクトに格納された節本文にも対応します。ネストした断片は読みやすい空白で連結されます。ライブプロバイダーが HTTP エラーを返した場合、CLI stderr にはステータス、読み取れるプロバイダーエラー項目または短く正規化されたプレーンテキスト本文、そして `Retry-After` 値があればそれも含まれます。

## データとライセンス

Bible Skill はこのリポジトリに聖書本文を含めません。利用者は各翻訳の条件を守る責任があります。ライブフォールバックは bible-api.com を正確な箇所検索にのみ使います。bible-api.com から聖書全体を一括ダウンロードしないでください。

## 開発

実行時コードは Python 3.11+ と標準ライブラリを使い、HTTP クライアントには `urllib` を使います。テストでは聖書本文ではなく、小さな人工フィクスチャを使います。

準備済みの開発環境で次のチェックを実行します：

```sh
ruff check .
ruff format --check .
pytest -q
python -m build
```

## テスト

テストスイートは、参照解析、ローカルメタデータ検索、ローカル箇所検索、キャッシュチェックサム検証、キャッシュマニフェスト検査、ローカル Markdown と USFM 出力、比較エクスポート、Free Use Bible API レスポンスの正規化、プロバイダーのエンドポイント、タイムアウト/リトライ動作とエラーフィクスチャ、保存/ダウンロード動作、CLI 出力、生成されるスキル本文をカバーします。

## ロードマップ

Bible Skill は現在、成長プロジェクトとして管理し、週 1 回の集中セッションを目安にしています。完了レビュー、保守トリガー、運用ペースのルールは [ROADMAP.md](ROADMAP.md) を参照してください。

現在のロードマップの重点：

- ライブプロバイダーの耐障害性を高め、有界リトライとエラー時の挙動を文書化します。
- Agent がインストール済みローカル箇所に依存する前に、キャッシュ/インポート検証を強化します。
- 手動検証前にレジストリインストール経路を主張せず、パッケージ公開の準備状況チェックを整えます。

## コントリビュート

コントリビューションを歓迎します。変更は小さく、振る舞いテストで保護し、翻訳ライセンスを尊重してください。[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

MIT。詳しくは [LICENSE](LICENSE) を参照してください。

このプロジェクトは AI の支援を受けて保守されていますが、プロジェクトの振る舞いはテストとソースレビューで検証されています。
