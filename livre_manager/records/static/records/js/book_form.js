/* static/js/book_form.js */

import { normalizeDate, InvalidFormatError, InvalidValueError } from './fuzzy-datetime/index.js';

(() => {

	function showWarning(field, message) {
		// 入力欄に対するエラーメッセージを表示する。
		let warningBox = field.parentNode.querySelector(':scope > .warning-message');
		if (message) {
			field.classList.add('invalid-input'); // エラークラスを追加
			if (!warningBox) {
				warningBox = document.createElement("div");
				warningBox.style.color = "red";
				warningBox.classList.add('warning-message');
				field.parentNode.appendChild(warningBox);
			}

			warningBox.textContent = message;
			warningBox.style.display = 'block';
		} else {
			field.classList.remove('invalid-input'); // エラークラスを削除
			if (warningBox) {
				warningBox.style.display = 'none';
			}
		}
	}

	// フォームセット関連の処理をまとめる
	const formsetManager = {
		prefix: 'authors', // フォームセットのプレフィックス
		MIN_INITIAL_ROWS: 3, // 初期表示時の最小行数

		init() {
			this.itemsContainer = document.getElementById('items-container')?.getElementsByTagName('tbody')[0];
			if (!this.itemsContainer) {
				return; // 著者フォームセットがない場合は何もしない
			}

			this.managementForm = document.getElementById(`id_${this.prefix}-TOTAL_FORMS`);
			this.emptyFormTemplate = document.getElementById('empty-form-template');
			this.addItemRowButton = document.getElementById('add-item-row-button');

			if (!this.managementForm || !this.emptyFormTemplate || !this.addItemRowButton) {
				console.error('Formset-related elements not found for authors.');
				return;
			}

			// handleDeleteRow の this を束縛
			this.handleDeleteRow = this.handleDeleteRow.bind(this);

			this.addItemRowButton.addEventListener('click', () => this.addRow());

			this.attachInitialDeleteRowListeners();
			this.attachInitialMoveRowListeners();
			this.updateOrderFields(); // 初期ロード時にも順序を更新
			this.updateMoveButtonsState();

			// 初期表示時に表示されている行が0個の場合、空の行を規定数になるまで追加する
			const visibleRows = this.itemsContainer.querySelectorAll('.author:not([style*="display: none"])');
			for (let i = visibleRows.length; i < this.MIN_INITIAL_ROWS; i++) {
				this.addRow();
			}
		},

		addRow() {
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

			// orderを設定
			const orderInput = newRow.querySelector(`input[name^="${this.prefix}-"][name$="-order"]`);
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
		 * 指定された行が空（ユーザーによる入力がない）かどうかを判定します。
		 * @param {HTMLElement} row - 判定対象の <tr> 要素。
		 * @returns {boolean} 行が空の場合は true, それ以外は false。
		 */
		isRowEmpty(row) {
			const fieldsToCheck = [
				'author_name',
			];

			for (const fieldName of fieldsToCheck) {
				const input = row.querySelector(`[name^="${this.prefix}-"][name$="-${fieldName}"]`);
				if (input && input.value.trim() !== '') {
					return false; // データが入力されているフィールドを発見
				}
			}

			return true; // すべての主要フィールドが空
		},

		handleDeleteRow(event) {
			const row = event.target.closest('.author');
			if (!row) {
				return;
			}

			// 行に何らかの値が入力されている場合は確認ダイアログを表示する。
			if (!this.isRowEmpty(row)) {
				const authorNameInput = row.querySelector(`[name^="${this.prefix}-"][name$="-author_name"]`);
				const authorName = authorNameInput ? authorNameInput.value.trim() : '';
				const itemInfo = authorName ? `「${authorName}」` : '';
				const confirmMessage = `著者${itemInfo}を削除しますか？`;

				if (!window.confirm(confirmMessage)) {
					// 削除キャンセル
					return;
				}
			}

			// 削除の実行
			const deleteInput = row.querySelector(`input[name^="${this.prefix}-"][name$="-DELETE"]`);
			if (deleteInput) {
				deleteInput.value = 'true';
			}
			row.style.display = 'none';
			this.updateOrderFields();
			this.updateMoveButtonsState();

			// 表示されている行がなくなったら、新しい空の行を追加する
			const visibleRows = this.itemsContainer.querySelectorAll('.author:not([style*="display: none"])');
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
			const row = event.target.closest('.author');
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
			const visibleRows = Array.from(this.itemsContainer.querySelectorAll('.author:not([style*="display: none"])'));
			visibleRows.forEach((row, index) => {
				const orderInput = row.querySelector(`input[name^="${this.prefix}-"][name$="-order"]`);
				if (orderInput) {
					orderInput.value = index;
				}
			});
		},

		// 最初と最後の行の移動ボタンを無効化/有効化する
		updateMoveButtonsState() {
			const visibleRows = Array.from(this.itemsContainer.querySelectorAll('.author:not([style*="display: none"])'));
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
		const publicationDateInput = document.getElementById('id_publication_date_str');

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
		function validatePublicationDate() {
			const val = publicationDateInput.value.trim();
			let msg = null;
			let normalizedDate = null;

			if (val !== '') {
				try {
					normalizedDate = normalizeDate(val, { requiredPrecision: 'year' });
				} catch (e) {
					if (e instanceof InvalidFormatError) {
						// フォーマットエラー
						msg = '「YYYY/MM/DD」の形式で入力してください。（月、日は省略可能）';
					} else if (e instanceof InvalidValueError) {
						// 値エラー
						msg = '存在しない日付です。';
					} else {
						// その他のエラー
						throw e; // 予期しないエラーは再スロー
					}
				}
			}

			if (msg !== null) {
				// 不正データ
				showWarning(publicationDateInput, 'エラー: ' + msg);
				errors.set('publicationDate', [msg, publicationDateInput]);
			} else {
				// 正常
				if (normalizedDate)
					publicationDateInput.value = normalizedDate;
				showWarning(publicationDateInput, '');
				errors.delete('publicationDate');
			}
		}

		validations['publicationDate'] = {
			validator: validatePublicationDate, targets: [publicationDateInput]
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

		// フォームセット管理を初期化
		formsetManager.init();

		/* end: エラー検証 */
	});
})();
