// records/static/records/js/receipt_ocr.js

document.addEventListener('DOMContentLoaded', function () {
	const uploadReceiptButton = document.getElementById('upload-receipt-button');
	const receiptImageUpload = document.getElementById('receipt-image-upload');
	const ocrStatusDiv = document.getElementById('ocr-status');
	const loadingIndicator = document.getElementById('loading-indicator');
	const ocrResultMessage = document.getElementById('ocr-result-message');
	// ISBNのみを表示するリスト
	const detectedIsbnsList = document.getElementById('detected-isbns-list');

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
			ocrResultMessage.textContent = '画像を処理中... (数分かかる場合があります)';
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
					const detectedIsbns = [];

					if (receipt && receipt.items && receipt.items.length > 0) {
						receipt.items.forEach(item => {
							if (item.isbn) {
								const listItem = document.createElement('li');
								listItem.textContent = item.isbn;
								detectedIsbnsList.appendChild(listItem);
								detectedIsbns.push(item.isbn);
							}
						});
					}

					if (detectedIsbns.length > 0) {
						// acquisition_form.js の関数を呼び出して一括で追加
						if (window.livre && typeof window.livre.fillOrAddIsbnRows === 'function') {
							window.livre.fillOrAddIsbnRows(detectedIsbns);
						} else {
							console.error('livre.fillOrAddIsbnRows function is not available.');
						}
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
});