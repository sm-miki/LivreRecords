// records/static/records/js/receipt_ocr.js

document.addEventListener('DOMContentLoaded', function () {
	const uploadReceiptButton = document.getElementById('upload-receipt-button');
	const receiptImageUpload = document.getElementById('receipt-image-upload');
	const ocrStatusDiv = document.getElementById('ocr-status');
	const loadingIndicator = document.getElementById('loading-indicator');
	const ocrResultMessage = document.getElementById('ocr-result-message');
	const detectedIsbnsList = document.getElementById('detected-isbns-list'); // This will still display just ISBNs
	const itemsContainer = document.getElementById('items-container').getElementsByTagName('tbody')[0]; // Target tbody for adding rows
	const managementForm = document.getElementById('id_items-TOTAL_FORMS'); // Get the total forms input

	// Function to get CSRF token from the DOM
	function getCookie(name) {
		let cookieValue = null;
		if (document.cookie && document.cookie !== '') {
			const cookies = document.cookie.split(';');
			for (let i = 0; i < cookies.length; i++) {
				const cookie = cookies[i].trim();
				// Does this cookie string begin with the name we want?
				if (cookie.substring(0, name.length + 1) === (name + '=')) {
					cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
					break;
				}
			}
		}
		return cookieValue;
	}

	if (uploadReceiptButton && receiptImageUpload) {
		uploadReceiptButton.addEventListener('click', function () {
			const file = receiptImageUpload.files[0];
			if (!file) {
				ocrResultMessage.textContent = 'ファイルを選択してください。';
				ocrStatusDiv.style.display = 'block';
				return;
			}

			ocrStatusDiv.style.display = 'block';
			loadingIndicator.style.display = 'inline';
			ocrResultMessage.textContent = '画像を処理中...';
			detectedIsbnsList.innerHTML = ''; // Clear previous results

			const formData = new FormData();
			formData.append('receipt_image', file);

			// Get CSRF token
			const csrftoken = getCookie('csrftoken');

			fetch('/records/acquisition/receipt_ocr/', {
				method: 'POST',
				body: formData,
				headers: {
					'X-CSRFToken': csrftoken, // Include CSRF token in headers
				},
			})
				.then(response => {
					loadingIndicator.style.display = 'none';
					if (!response.ok) {
						throw new Error(`HTTP error! status: ${response.status}`);
					}
					return response.json();
				})
				.then(data => {
					if (data.success) {
						ocrResultMessage.textContent = 'OCR処理が完了しました！';
						// Now expecting data.items which is a list of dictionaries
						const receipt = data.receipt;
						if (receipt && receipt.items && receipt.items.length > 0) {
							receipt.items.forEach(item => {
								if (item.isbn) { // Check if 'isbn' key exists in the item
									const listItem = document.createElement('li');
									listItem.textContent = item.isbn;
									detectedIsbnsList.appendChild(listItem);

									// Automatically add new item rows for each detected ISBN
									// Pass the whole item object if you want to use other fields later
									addAcquiredItemRow(item.isbn);
								}
							});
						} else {
							ocrResultMessage.textContent += ' ISBNは検出されませんでした。';
						}
					} else {
						ocrResultMessage.textContent = `OCR処理に失敗しました: ${data.message || '不明なエラー'}`;
					}
				})
				.catch(error => {
					loadingIndicator.style.display = 'none';
					ocrResultMessage.textContent = `OCR処理中にエラーが発生しました: ${error}`;
					console.error('Error during OCR upload:', error);
				});
		});
	}

	// Function to add a new acquired item row dynamically for detected ISBNs
	function addAcquiredItemRow(isbn = '') { // Only taking ISBN for now, but could take a full item object
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

		// Update the total forms count in the management form
		managementForm.value = totalForms + 1;

		// Re-attach event listeners for newly added delete buttons
		attachDeleteRowListeners();
	}

	// Existing "Add Item" button listener (from acquisition_form.js, assuming it exists)
	const addItemRowButton = document.getElementById('add-item-row-button');
	if (addItemRowButton) {
		addItemRowButton.addEventListener('click', function () {
			addAcquiredItemRow(''); // Add a new empty row
		});
	}

	// Function to attach delete row listeners (needed for dynamically added rows)
	function attachDeleteRowListeners() {
		document.querySelectorAll('.delete-row-button').forEach(button => {
			// Remove previous listeners to prevent duplicates
			button.removeEventListener('click', handleDeleteRow);
			button.addEventListener('click', handleDeleteRow);
		});
	}

	// Handler for delete row button
	function handleDeleteRow(event) {
		const row = event.target.closest('.acquired-item');
		if (row) {
			// Mark the DELETE checkbox for the formset to handle deletion on save
			const deleteInput = row.querySelector('input[name$="-DELETE"]');
			if (deleteInput) {
				deleteInput.checked = true;
			}
			// Hide the row visually
			row.style.display = 'none';
		}
	}

	// Initial attachment of delete row listeners for existing rows
	attachDeleteRowListeners();
});