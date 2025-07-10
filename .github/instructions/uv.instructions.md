# uvに関するインストラクション

uvはpythonの仮想環境とパッケージ管理に使われます。

## バージョンを確認する

- uvがインストール済みであることを確認します
- uvのバージョンを確認します

```shell
uv --version
```

## プロジェクトを初期化する

- uvのプロジェクトを初期化します

```shell
# プロジェクトのディレクトリを作成する
mkdir {uvのプロジェクト名}
# プロジェクトのディレクトリに移動する
cd {uvのプロジェクト名}
# uv initコマンドで仮想環境を初期化する
# --pythonオプションでpythonのバージョンをマイナーバージョンまで指定する
uv init . --python 3.12
```

- {uvのプロジェクト名}に`pyproject.toml`が生成される
- `pyproject.toml`の以下の箇所を変更し、マイナーバージョンが固定されるようにする

```toml
# pythonのバージョンを`3.12`に固定する例
# 変更前
requires-python = ">=3.12"

# 変更後
# <3.13を追加することで、意図せずマイナーバージョンが上がることを防ぐ
requires-python = ">=3.12,<3.13"
```

- 仮想環境を作成する

```shell
uv sync
```

- 仮想環境が作成されたことを確認する

```shell
uv run main.py
```

- 不要なサンプルコードを削除する

```shell
rm main.py
```

## ライブラリの追加・削除を行う

### 追加を行う

```shell
# 追加する前の確認をする
uv tree

# メインの依存パッケージの場合
uv add django pandas

# 開発・CIに利用するパッケージの場合
uv add --group dev ruff pytest

# 追加されたか確認をする
uv tree
```

### 削除を行う

```shell
# 削除する前の確認をする
uv tree

# メインの依存パッケージの場合
uv remove django pandas

# 開発・CIに利用するパッケージの場合
uv remove --group dev ruff pytest

# 削除されたか確認をする
uv tree
```

## ライブラリのバージョンアップを行う