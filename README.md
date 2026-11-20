# GitHub repository stats

GitHub REST APIからリポジトリの主要言語とスター数を取得し、SQLiteの
`repositories` テーブルに保存する小さなPythonツールです。

## Setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

引数を省略すると `google/guava` を取得します。

```sh
python scraper.py
```

別のリポジトリやデータベースを指定できます。

```sh
python scraper.py pallets/cargo
python scraper.py pallets/cargo --database ./data/repositories.db
```

保存先のテーブルは `name`（`OWNER/REPO`）、`language`、`stars` の3列です。
同じリポジトリを再度取得すると、既存の行を最新値で更新します。
GitHubのレート制限やネットワークエラーが発生した場合は、内容を標準エラーに表示して終了します。
