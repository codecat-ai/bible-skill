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
- ID、名前、言語、ライセンス URL、ソース URL でインストール済み翻訳のメタデータをローカル検索します。
- 書、章、単節、節範囲、同一書内の章をまたぐ範囲でローカル箇所を検索します。
- ローカル検索結果を最小で決定的な USFM 風テキストとして出力します。
- 2 つ以上のインストール済み翻訳で同じローカル箇所をテキスト、JSON、Markdown、または CSV で比較します。
- 翻訳全体をダウンロードせずに正確な箇所を調べるため、bible-api.com をライブフォールバックとして使え、テキスト、JSON、Markdown、CSV で出力できます。
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
python -m pip install -e .
bible-skill --help
```

`pip install bible-skill`、`uvx bible-skill`、または同様のレジストリ用コマンドは使わないでください。レジストリ公開版はまだありません。

## クイックスタート

```sh
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill installed --data-dir ./data
bible-skill search english --data-dir ./data
bible-skill search license.example --data-dir ./data --json
bible-skill query web "John 3:16" --data-dir ./data
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --json
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --usfm
bible-skill compare "John 3:16" web kjv --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --markdown
bible-skill compare "John 3:16" web kjv --data-dir ./data --csv
bible-skill live "John 3:16" --translation web
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

## 設定

`--data-dir` でダウンロード済み翻訳の保存先を指定します。指定しない場合、Bible Skill はプラットフォームに合ったユーザーデータディレクトリを使います。ダウンロード記録には、翻訳メタデータ、ソース URL、取得時刻、提供元が返すライセンス URL が含まれます。`search` と `compare` コマンドはインストール済みのローカル翻訳だけを読むため、ローカルメタデータ検索や比較を行う各翻訳を先にダウンロードしてください。

ライブフォールバックでは、`--json` で bible-api.com の生レスポンスを出力でき、`--markdown` でノートに貼り付けやすい形式を出力でき、`--csv` で `reference`、`translation`、`verse_reference`、`text` 列を持つ表計算向けの行を出力できます。`--json`、`--markdown`、`--csv` は同時に指定できません。

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

テストスイートは、参照解析、ローカルメタデータ検索、ローカル箇所検索、USFM 出力と比較エクスポート、Free Use Bible API レスポンスの正規化、プロバイダーのエンドポイント、保存/ダウンロード動作、CLI 出力、生成されるスキル本文をカバーします。

## ロードマップ

- より多くのプロバイダーデータ形状に対応し、ライブ CSV のフォールバック項目を含めて、プロバイダーごとのライブレスポンス差異を記録します。
- 手動のレジストリ検証後にパッケージ公開を準備します。

## コントリビュート

コントリビューションを歓迎します。変更は小さく、振る舞いテストで保護し、翻訳ライセンスを尊重してください。[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

MIT。詳しくは [LICENSE](LICENSE) を参照してください。

このプロジェクトは AI の支援を受けて保守されていますが、プロジェクトの振る舞いはテストとソースレビューで検証されています。
