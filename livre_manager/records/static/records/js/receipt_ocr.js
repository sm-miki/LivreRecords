// records/static/records/js/receipt_ocr.js

document.addEventListener('DOMContentLoaded', function () {
	const uploadReceiptButton = document.getElementById('upload-receipt-button');
	const receiptImageUpload = document.getElementById('receipt-image-upload');
	const ocrStatusDiv = document.getElementById('ocr-status');
	const loadingIndicator = document.getElementById('loading-indicator');
	const ocrResultMessage = document.getElementById('ocr-result-message');
	// ISBNのみを表示するリスト
	const detectedIsbnsList = document.getElementById('detected-isbns-list');
	// 行追加先のtbodyを指定
	const itemsContainer = document.getElementById('items-container').getElementsByTagName('tbody')[0];
	// フォーム数管理用のinputを取得
	const managementForm = document.getElementById('id_items-TOTAL_FORMS');

	/**
	 * cookieを取得する関数
	 * @param {*} name cookie名
	 * @returns {string|null} cookieの値。存在しない場合はnull。
	 */
	function getCookie(name) {
		let cookieValue = null;
		if (document.cookie && document.cookie !== '') {
			const cookies = document.cookie.split(';');
			for (let i = 0; i < cookies.length; i++) {
				const cookie = cookies[i].trim();
				// 指定した名前で始まるcookieかどうか判定
				if (cookie.substring(0, name.length + 1) === (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}

	/**
	 * 画像ファイルをリサイズする関数。アップロード前に画像のサイズを調整するために使用される。
	 * @param {File} file 画像ファイル。
	 * @param {number} maxWidth 画像幅の最大値。
	 * @param {number} maxHeight 画像高さの最大値。
	 * @param {number} quality JPEG画像の品質（0から1の範囲）。
	 * @returns {Promise<Blob>} リサイズされた画像のBlobオブジェクトを返すPromise。
	 */
	function resizeImage(file, maxWidth, maxHeight, quality) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = (e) => {
				const img = new Image();
				img.onload = () => {
					let width = img.width;
					let height = img.height;

					// 画像が既に十分小さい場合はリサイズしない
					if (width <= maxWidth && height <= maxHeight) {
						resolve(file);
						return;
					}

					if (width > height) {
						if (width > maxWidth) {
							height *= maxWidth / width;
							width = maxWidth;
						}
					} else {
						if (height > maxHeight) {
							width *= maxHeight / height;
							height = maxHeight;
						}
					}

					const canvas = document.createElement('canvas');
					canvas.width = width;
					canvas.height = height;
					const ctx = canvas.getContext('2d');
					ctx.drawImage(img, 0, 0, width, height);

					canvas.toBlob((blob) => {
						resolve(blob);
					}, 'image/jpeg', quality);
				};
				img.onerror = reject;
				img.src = e.target.result;
			};
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	}

	/* メイン処理 */

	if (uploadReceiptButton && receiptImageUpload) {
		uploadReceiptButton.addEventListener('click', async function () {
			const file = receiptImageUpload.files[0];
			const MAX_FILE_SIZE = 20 * 1024 * 1024; // 最大ファイルサイズ20MB

			if (!file) {
				ocrResultMessage.textContent = 'ファイルを選択してください。';
				ocrStatusDiv.style.display = 'block';
				return;
			}

			if (!file.type.startsWith('image/')) {
				ocrResultMessage.textContent = '画像ファイルを選択してください。';
				ocrStatusDiv.style.display = 'block';
				return;
			}

			if (file.size > MAX_FILE_SIZE) {
				ocrResultMessage.textContent = `ファイルサイズが大きすぎます。${MAX_FILE_SIZE / 1024 / 1024}MB以下のファイルを選択してください。`;
				ocrStatusDiv.style.display = 'block';
				return;
			}

			ocrStatusDiv.style.display = 'block';
			loadingIndicator.style.display = 'inline';
			ocrResultMessage.textContent = '画像を処理中...';
			detectedIsbnsList.innerHTML = ''; // 前回の結果をクリア

			try {
				const resizedBlob = await resizeImage(file, 2000, 2000, 0.9);

				const formData = new FormData();
				formData.append('receipt_image', resizedBlob, file.name);
				const csrftoken = getCookie('csrftoken');

				const response = await fetch('/acquisition/receipt_ocr/', {
					method: 'POST',
					body: formData,
					headers: { 'X-CSRFToken': csrftoken },
				});

				loadingIndicator.style.display = 'none';
				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}

				const data = await response.json();
				if (data.success) {
					ocrResultMessage.textContent = 'OCR処理が完了しました！';
					const receipt = data.receipt;
					if (receipt && receipt.items && receipt.items.length > 0) {
						receipt.items.forEach(item => {
							if (item.isbn) {
								const listItem = document.createElement('li');
								listItem.textContent = item.isbn;
								detectedIsbnsList.appendChild(listItem);
								addAcquiredItemRow(item.isbn);
							}
						});
					} else {
						ocrResultMessage.textContent += ' ISBNは検出されませんでした。';
					}
				} else {
					ocrResultMessage.textContent = `OCR処理に失敗しました: ${data.message || '不明なエラー'}`;
				}
			} catch (error) {
				loadingIndicator.style.display = 'none';
				ocrResultMessage.textContent = `OCR処理中にエラーが発生しました: ${error}`;
				console.error('Error during OCR upload:', error);
			}
		});
	}

	// 検出されたISBN用の新しい取得アイテム行を動的に追加する関数
	function addAcquiredItemRow(isbn = '') {
		const totalForms = parseInt(managementForm.value);
		const newFormIndex = totalForms;

		const newRow = document.createElement('tr');
		newRow.className = 'acquired-item';
		newRow.innerHTML = `
			<td><input type="hidden" name="items-${newFormIndex}-id" id="id_items-${newFormIndex}-id">
				<input type="hidden" name="items-${newFormIndex}-acquisition" id="id_items-${newFormIndex}-acquisition">
				<input type="hidden" name="items-${newFormIndex}-DELETE" id="id_items-${newFormIndex}-DELETE">
				<input type="hidden" name="items-${newFormIndex}-order" id="id_items-${newFormIndex}-order" value="${newFormIndex}">
				<select name="items-${newFormIndex}-item_type" class="form-control" id="id_items-${newFormIndex}-item_type">
					<option value="book" selected>書籍</option>
					<option value="other">その他</option>
				</select>
			</td>
			<td><input type="text" name="items-${newFormIndex}-item_id" value="${isbn}" class="form-control" id="id_items-${newFormIndex}-item_id"></td>
			<td><input type="text" name="items-${newFormIndex}-genre_code" class="form-control" id="id_items-${newFormIndex}-genre_code"></td>
			<td><input type="text" name="items-${newFormIndex}-description" class="form-control" id="id_items-${newFormIndex}-description"></td>
			<td><input type="number" name="items-${newFormIndex}-price" class="form-control" id="id_items-${newFormIndex}-price"></td>
			<td><input type="number" name="items-${newFormIndex}-net_price" class="form-control" id="id_items-${newFormIndex}-net_price"></td>
			<td><input type="number" name="items-${newFormIndex}-tax" class="form-control" id="id_items-${newFormIndex}-tax"></td>
			<td><input type="number" name="items-${newFormIndex}-quantity" value="1" class="form-control" id="id_items-${newFormIndex}-quantity"></td>
			<td><input type="text" name="items-${newFormIndex}-user_memo" class="form-control" id="id_items-${newFormIndex}-user_memo"></td>
			<td><button type="button" class="delete-row-button">削除</button></td>
		`;
		itemsContainer.appendChild(newRow);

		// 管理フォームのフォーム数を更新
		managementForm.value = totalForms + 1;

		// 新しく追加された削除ボタンにイベントリスナーを再度付与
		attachDeleteRowListeners();
	}

	// 既存の「アイテム追加」ボタンのリスナー（acquisition_form.js由来想定）
	const addItemRowButton = document.getElementById('add-item-row-button');
	if (addItemRowButton) {
		addItemRowButton.addEventListener('click', function () {
			addAcquiredItemRow(''); // 空行を追加
		});
	}

	// 削除ボタンのイベントリスナーを付与する関数（動的追加行にも必要）
	function attachDeleteRowListeners() {
		document.querySelectorAll('.delete-row-button').forEach(button => {
			// 重複防止のため以前のリスナーを削除
			button.removeEventListener('click', handleDeleteRow);
			button.addEventListener('click', handleDeleteRow);
		});
	}

	// 削除ボタンのイベントハンドラ
	function handleDeleteRow(event) {
		const row = event.target.closest('.acquired-item');
		if (row) {
			// フォームセットのDELETEチェックボックスをONにして保存時に削除扱いにする
			const deleteInput = row.querySelector('input[name$="-DELETE"]');
			if (deleteInput) {
				deleteInput.checked = true;
			}
			// 行を画面上で非表示にする
			row.style.display = 'none';
		}
	}

	// 既存行の削除ボタンリスナーを初期的に付与
	attachDeleteRowListeners();
});