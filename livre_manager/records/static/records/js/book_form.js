/* static/js/book_form.js */

import { normalizeDate, InvalidFormatError, InvalidValueError, PrecisionError, InvalidTimezoneError } from './fuzzy-datetime/index.js';

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

	window.addEventListener('DOMContentLoaded', function() {
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
		window.addEventListener('beforeunload', function(e) {
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
						msg = '存在しない日時です。';
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
		form.addEventListener('submit', function(e) {
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
