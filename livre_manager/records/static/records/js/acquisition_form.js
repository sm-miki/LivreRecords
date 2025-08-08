/* static/js/acquisition_form.js */

						// 精度エラー
						// 精度エラー
import { normalizeDateTime, InvalidFormatError, InvalidValueError, PrecisionError, InvalidTimezoneError } from './fuzzy-datetime/index.js';

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

	window.addEventListener('DOMContentLoaded', function () {
		// 入手日時の入力欄とエラー表示用要素、Submit ボタンを取得
		const form = document.querySelector('form');
		const acquisitionDateInput = document.getElementById('id_acquisition_date_str');
		const totalInput = document.getElementById('id_total');
		const subtotalInput = document.getElementById('id_subtotal');
		const taxInput = document.getElementById('id_tax');
		const extraFeeInput = document.getElementById('id_extra_fee');

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