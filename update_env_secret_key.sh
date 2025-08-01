#!/bin/bash

# OSの種類を判定
if [[ "$OSTYPE" == "darwin"* ]]; then
	# MacOS
	OS_TYPE="MacOS"
else
	# その他のUNIX系OS（主にLinux）
	OS_TYPE="Other"
fi

# DjangoでSECRET_KEYを生成
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

echo SECRET_KEY

# .envファイルのパスを指定
ENV_FILE=".env"

# .envファイルの存在確認
if [ -f "$ENV_FILE" ]; then
	echo ".envファイルが見つかりました。SECRET_KEYを更新します。"

	# OSに応じてsedコマンドを実行
	if [ "$OS_TYPE" == "MacOS" ]; then
		sed -i '' '/^SECRET_KEY=/d' "$ENV_FILE"
	else
		sed -i '/^SECRET_KEY=/d' "$ENV_FILE"
	fi

	echo "SECRET_KEY=$SECRET_KEY" >> "$ENV_FILE"
	echo "SECRET_KEYを更新しました。"
else
	echo ".envファイルが見つかりません。新しく作成します。"
	echo "SECRET_KEY=$SECRET_KEY" > "$ENV_FILE"
	echo ".envファイルを作成し、SECRET_KEYを設定しました。"
fi

# 変更の確認
echo "更新後の.envファイルの内容:"
cat "$ENV_FILE"
