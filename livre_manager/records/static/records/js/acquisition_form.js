/* static/js/acquisition_form.js */

import { normalizeDateTime, InvalidFormatError, InvalidValueError, PrecisionError, InvalidTimezoneError } from './fuzzy-datetime/index.js';

// グローバルな名前空間を作成
window.livre = window.livre || {};

(() => {
	function showWarning(field, message) {
		// 入力欄に対するエラーメッセージを表示する。
		var warningBox = field.parentNode.querySelector(':scope > .warning-message');
		if (message) {
			if (!warningBox) {
				warningBox = document.createElement("div");
				warningBox.style.color = "red";
				warningBox.classList.add('warning-message');
				field.parentNode.appendChild(warningBox);
			}

			warningBox.textContent = message;
			warningBox.style.display = 'block';
		} else if (warningBox) {
			warningBox.style.display = 'none';
		}
	}

	// フォームセット関連の処理をまとめる
	const formsetManager = {
		init() {
			this.itemsContainer = document.getElementById('items-container').getElementsByTagName('tbody')[0];
			this.managementForm = document.getElementById('id_items-TOTAL_FORMS');
			this.emptyFormTemplate = document.getElementById('empty-form-template');
			this.addItemRowButton = document.getElementById('add-item-row-button');

			// handleDeleteRow の this を束縛
			this.handleDeleteRow = this.handleDeleteRow.bind(this);

			if (this.addItemRowButton) {
				this.addItemRowButton.addEventListener('click', () => this.addRow());
			}

			this.attachInitialDeleteRowListeners();
			this.attachInitialMoveRowListeners();
			this.updateOrderFields(); // 初期ロード時にも順序を更新
			this.updateMoveButtonsState();

			// 初期表示時に表示されている行が0個の場合、空の行を1つ追加する
			const visibleRows = this.itemsContainer.querySelectorAll('.acquired-item:not([style*="display: none"])');
			if (visibleRows.length === 0) {
				this.addRow();
			}

			// グローバルに公開
			window.livre.addRow = this.addRow.bind(this);
			window.livre.fillOrAddIsbnRows = this.fillOrAddIsbnRows.bind(this);
		},

		addRow(data = {}) {
			const totalForms = parseInt(this.managementForm.value);
			const newFormIndex = totalForms;

			// <template> タグからコンテンツを複製
			const newRowFragment = this.emptyFormTemplate.content.cloneNode(true);
			const newRow = newRowFragment.querySelector('tr'); // <tr>要素を取得

			// 複製した行の input, select, textarea 要素の属性を更新
			newRow.querySelectorAll('input, select, textarea').forEach(input => {
				if (input.name) {
					input.name = input.name.replace(/__prefix__/g, newFormIndex);
				}
				if (input.id) {
					input.id = input.id.replace(/__prefix__/g, newFormIndex);
				}
			});

			// データを新しい行に設定
			if (data.isbn) {
				newRow.querySelector(`input[name="items-${newFormIndex}-item_id"]`).value = data.isbn;
			}
			// quantityのデフォルト値を1に設定
			const quantityInput = newRow.querySelector(`input[name="items-${newFormIndex}-quantity"]`);
			if (quantityInput && !quantityInput.value) {
				quantityInput.value = '1';
			}
			// orderを設定
			const orderInput = newRow.querySelector(`input[name="items-${newFormIndex}-order"]`);
			if (orderInput) {
				orderInput.value = newFormIndex;
			}

			// itemsContainer (tbody) に新しい行を追加
			this.itemsContainer.appendChild(newRow);

			// 管理フォームのフォーム数を更新
			this.managementForm.value = totalForms + 1;

			// 新しく追加された削除ボタンにイベントリスナーを付与
			const deleteButton = newRow.querySelector('.delete-row-button');
			if (deleteButton) {
				deleteButton.addEventListener('click', this.handleDeleteRow);
			}

			// 新しく追加された移動ボタンにイベントリスナーを付与
			newRow.querySelector('.move-up-button')?.addEventListener('click', (e) => this.handleMoveRow(e, 'up'));
			newRow.querySelector('.move-down-button')?.addEventListener('click', (e) => this.handleMoveRow(e, 'down'));

			this.updateOrderFields();
			this.updateMoveButtonsState();

			return newRow;
		},

		/**
		 * 複数のISBNをフォームセットに設定する。
		 * データが入力されている最後の行より後ろにある空行を優先的に使用し、
		 * 足りない場合は新しい行を追加する。
		 * @param {string[]} isbns - 追加するISBNの配列。
		 */
		fillOrAddIsbnRows(isbns) {
			if (!isbns || isbns.length === 0) {
				return;
			}

			const itemRows = Array.from(this.itemsContainer.querySelectorAll('.acquired-item'));
			let lastDataRowIndex = -1;

			// ISBNが入力されている最後の行のインデックスを見つける
			itemRows.forEach((row, index) => {
				if (row.style.display === 'none') {
					return; // 削除済みの行はスキップ
				}
				const isbnInput = row.querySelector('input[name$="-item_id"]');
				if (isbnInput && isbnInput.value.trim() !== '') {
					lastDataRowIndex = index;
				}
			});

			// 最後のデータ行の「後」にある、利用可能な空行を探す
			const availableEmptyRows = [];
			for (let i = lastDataRowIndex + 1; i < itemRows.length; i++) {
				const row = itemRows[i];
				if (row.style.display !== 'none') {
					const isbnInput = row.querySelector('input[name$="-item_id"]');
					// ISBN入力欄が空の行を対象とする
					if (isbnInput && isbnInput.value.trim() === '') {
						availableEmptyRows.push(row);
					}
				}
			}

			let isbnIndex = 0;
			// 見つかった空行にISBNを順番に埋めていく
			for (const row of availableEmptyRows) {
				if (isbnIndex >= isbns.length) break;
				const isbnInput = row.querySelector('input[name$="-item_id"]');
				if (isbnInput) {
					isbnInput.value = isbns[isbnIndex++];
				}
			}

			// それでもISBNが残っている場合は、新しい行を追加する
			for (let i = isbnIndex; i < isbns.length; i++) {
				this.addRow({ isbn: isbns[i] });
			}
		},

		/**
		 * 指定された行が空（ユーザーによる入力がない）かどうかを判定します。
		 * @param {HTMLElement} row - 判定対象の <tr> 要素。
		 * @returns {boolean} 行が空の場合は true, それ以外は false。
		 */
		isRowEmpty(row) {
			// ユーザーが入力する可能性のある主要なフィールドをチェックする。
			// これらのいずれかに値があれば、行は「空ではない」と見なす。
			const fieldsToCheck = [
				'item_id',
				'genre_code',
				'description',
				'price',
				'net_price',
				'tax',
				'user_memo'
			];

			for (const fieldName of fieldsToCheck) {
				const input = row.querySelector(`input[name$="-${fieldName}"]`);
				if (input && input.value.trim() !== '') {
					return false; // データが入力されているフィールドを発見
				}
			}

			return true; // すべての主要フィールドが空
		},

		handleDeleteRow(event) {
			const row = event.target.closest('.acquired-item');
			if (!row) {
				return;
			}

			// 行に何らかの値が入力されている場合は確認ダイアログを表示する。
			if (!this.isRowEmpty(row)) {
				// 行にデータがある場合は、確認ダイアログを表示
				const descriptionInput = row.querySelector('input[name$="-description"]');
				const itemIdInput = row.querySelector('input[name$="-item_id"]');
				const description = descriptionInput ? descriptionInput.value.trim() : '';
				const itemId = itemIdInput ? itemIdInput.value.trim() : '';
				const itemInfo = description ? `「${description}」` : (itemId ? `「ID: ${itemId}」` : '');
				const confirmMessage = itemInfo ? `項目${itemInfo}を削除しますか？` : 'この項目を削除しますか？';

				if (!window.confirm(confirmMessage)) {
					// 削除キャンセル
					return;
				}
			}

			// 削除の実行
			const deleteInput = row.querySelector('input[name$="-DELETE"]');
			if (deleteInput) {
				deleteInput.value = 'true';
			}
			row.style.display = 'none';
			this.updateOrderFields();
			this.updateMoveButtonsState();

			// 表示されている行がなくなったら、新しい空の行を追加する
			const visibleRows = this.itemsContainer.querySelectorAll('.acquired-item:not([style*="display: none"])');
			if (visibleRows.length === 0) {
				this.addRow();
			}
		},

		/**
		 * 行を上下に移動させるイベントハンドラ
		 * @param {Event} event - クリックイベント
		 * @param {string} direction - 'up' または 'down'
		 */
		handleMoveRow(event, direction) {
			const row = event.target.closest('.acquired-item');
			if (!row) {
				return;
			}

			if (direction === 'up') {
				let prevSibling = row.previousElementSibling;
				while (prevSibling && prevSibling.style.display === 'none') {
					prevSibling = prevSibling.previousElementSibling;
				}
				if (prevSibling) {
					this.itemsContainer.insertBefore(row, prevSibling);
				}
			} else if (direction === 'down') {
				let nextSibling = row.nextElementSibling;
				while (nextSibling && nextSibling.style.display === 'none') {
					nextSibling = nextSibling.nextElementSibling;
				}
				if (nextSibling) {
					this.itemsContainer.insertBefore(row, nextSibling.nextElementSibling);
				}
			}

			this.updateOrderFields();
			this.updateMoveButtonsState();
		},

		// 表示されている行に基づいてORDERフィールドの値を更新する
		updateOrderFields() {
			const visibleRows = Array.from(this.itemsContainer.querySelectorAll('.acquired-item:not([style*="display: none"])'));
			visibleRows.forEach((row, index) => {
				const orderInput = row.querySelector('input[name$="-order"]');
				if (orderInput) {
					orderInput.value = index;
				}
			});
		},

		// 最初と最後の行の移動ボタンを無効化/有効化する
		updateMoveButtonsState() {
			const visibleRows = Array.from(this.itemsContainer.querySelectorAll('.acquired-item:not([style*="display: none"])'));
			visibleRows.forEach((row, index) => {
				const upButton = row.querySelector('.move-up-button');
				const downButton = row.querySelector('.move-down-button');
				if (upButton) upButton.disabled = (index === 0);
				if (downButton) downButton.disabled = (index === visibleRows.length - 1);
			});
		},

		attachInitialDeleteRowListeners() {
			this.itemsContainer.querySelectorAll('.delete-row-button').forEach(button => {
				button.addEventListener('click', this.handleDeleteRow);
			});
		},

		attachInitialMoveRowListeners() {
			this.itemsContainer.querySelectorAll('.move-up-button').forEach(button => {
				button.addEventListener('click', (e) => this.handleMoveRow(e, 'up'));
			});
			this.itemsContainer.querySelectorAll('.move-down-button').forEach(button => {
				button.addEventListener('click', (e) => this.handleMoveRow(e, 'down'));
			});
		}
	};

	window.addEventListener('DOMContentLoaded', function () {
		// 入手日時の入力欄とエラー表示用要素、Submit ボタンを取得
		const form = document.querySelector('form');
		const acquisitionDateInput = document.getElementById('id_acquisition_date_str');
		const totalInput = document.getElementById('id_total');
		const subtotalInput = document.getElementById('id_subtotal');
		const taxInput = document.getElementById('id_tax');
		const extraFeeInput = document.getElementById('id_extra_fee');

		// フォームセット管理を初期化
		formsetManager.init();

		/* ダーティフラグの管理と離脱時の警告表示 */

		// フォームに変更があったかどうかのフラグ
		let formModified = false;

		form.addEventListener('change', () => {
			formModified = true;
		});
		form.addEventListener('input', () => {
			formModified = true;
		});

		// ページ離脱時の確認ダイアログ
		window.addEventListener('beforeunload', function (e) {
			if (formModified) {
				// ブラウザのデフォルトの確認メッセージを表示
				e.preventDefault();
				e.returnValue = ''; // 古いブラウザのために必要
			}
		});


		/* エラーデータ検証 */

		// フォーム全体のエラー状態を管理するフラグ
		const errors = new Map();		// id: [msg, focusBody]
		let validations = {};

		// 入力時（input）／フォーカスアウト時（blur）に検証
		function validateAcquisitionDate() {
			const val = acquisitionDateInput.value.trim();
			let msg = null;
			let normalizedDate = null;

			if (val !== '') {
				try {
					normalizedDate = normalizeDateTime(val, { requiredPrecision: 'day' });
				} catch (e) {
					if (e instanceof InvalidFormatError) {
						// フォーマットエラー
						msg = '「YYYY/MM/DD hh:mm:ss」の形式で入力してください。（時、分、秒は省略可能）';
					} else if (e instanceof InvalidValueError) {
						// 値エラー
						msg = '存在しない日時です。';
					} else if (e instanceof PrecisionError) {
						// 精度エラー
						msg = '少なくとも年月日を入力してください。';
					} else if (e instanceof InvalidTimezoneError) {
						// タイムゾーンエラー
						msg = '不明なタイムゾーンです。';
					} else {
						// その他のエラー
						throw e; // 予期しないエラーは再スロー
					}
				}
			}

			if (msg !== null) {
				// 不正データ
				showWarning(acquisitionDateInput, 'エラー: ' + msg);
				errors.set('acquisitionDate', [msg, acquisitionDateInput]);
			} else {
				// 正常
				if (normalizedDate)
					acquisitionDateInput.value = normalizedDate;
				showWarning(acquisitionDateInput, '');
				errors.delete('acquisitionDate');
			}
		}

		validations['acquisitionDate'] = {
			validator: validateAcquisitionDate, targets: [acquisitionDateInput]
		};

		function validateTotal() {
			const total = parseInt(totalInput.value.trim());
			const subtotal = parseInt(subtotalInput.value.trim());
			const tax = parseInt(taxInput.value.trim());
			const extraFee = parseInt(extraFeeInput.value.trim());

			if (!isNaN(total) && !isNaN(subtotal) && !isNaN(tax)
				&& total != subtotal + tax + (extraFee || 0)) {
				// 不正データ
				const msg = '支払金額が(税抜合計 + 税額 + 送料等)と一致しません。';
				showWarning(totalInput, msg);
				errors.set('tax', [msg, totalInput]);
			} else {
				// 正常
				showWarning(totalInput, '');
				errors.delete('tax');
			}
		}

		validations['tax'] = {
			validator: validateTotal, targets: [totalInput, subtotalInput, taxInput, extraFeeInput]
		};

		// データ検証のイベントリスナを登録
		for (let [name, v] of Object.entries(validations)) {
			for (let target of v.targets)
				target.addEventListener('change', v.validator);
		}

		function validate() {
			// すべての検証を実行する
			for (let [name, v] of Object.entries(validations)) {
				v.validator();
			}
			return errors.size != 0;
		}

		// フォーム送信時にチェック
		form.addEventListener('submit', function (e) {
			// 送信前に最終チェック
			if (validate() /* || 他のエラー */) {
				// エラーが発生したため送信キャンセル
				e.preventDefault();

				// フォーカスをエラー箇所へ移す
				[...errors][0][1][1].focus();

				// メッセージボックスを表示
				//				errorSummary = [...errors].map(([k, [msg, focusBody]]) => msg).join('\n');
				//				alert(errorSummary);
			} else {
				// エラーがない場合、フォームが送信されるので formModified を false に設定
				formModified = false;
			}
		});

		// ページロード後に一度チェックを走らせておく
		validate();

		/* end: エラー検証 */
	});
})();