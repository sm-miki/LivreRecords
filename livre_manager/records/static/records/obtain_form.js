// static/js/obtain_form.js

(() => {
	function validateDatetime(value) {
		// 日付フォーマットを検証する関数
		const datetimeReg = /^(?<year>\d{4})\/(?<month>\d{1,2})\/(?<day>\d{1,2})( +(?<hour>\d{1,2})(:(?<minute>\d{1,2})(:(?<second>\d{1,2}))?)?)?$/;
		let result = datetimeReg.exec(value);
		if (!result) {
			return false;
		}
		// 実在する日付かどうかもチェックしたい場合は以下のように Date オブジェクトを使う
		const parts = value.split('/');
		const year = parseInt(result.groups.year, 10);
		const month = result.groups.month ? parseInt(result.groups.month, 10) : 1;
		const day = result.groups.day ? parseInt(result.groups.day, 10) : 1;
		const hours = result.groups.hours ? parseInt(result.groups.hours, 10) : 0;
		const minutes = result.groups.minutes ? parseInt(result.groups.minutes, 10) : 0;
		const seconds = result.groups.seconds ? parseInt(result.groups.seconds, 10) : 0;
		const dt = new Date(year, month, day, hours, minutes, seconds);
		// 生成した日付オブジェクトを元の日付文字列と比較して「有効な日付かどうか」を判定
		return dt.getFullYear() === year && dt.getMonth() === month && dt.getDate() === day
			&& dt.getHours() === hours && dt.getMinutes() === minutes && dt.getSeconds() === seconds;
	}

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

	window.addEventListener('DOMContentLoaded', function() {
		// 1) 入手日時の入力欄とエラー表示用要素、Submit ボタンを取得
		const obtainDateInput = document.getElementById('id_obtain_date_str');
		const totalInput = document.getElementById('id_total');
		const subtotalInput = document.getElementById('id_subtotal');
		const taxInput = document.getElementById('id_tax');
		const extraFeeInput = document.getElementById('id_extra_fee');

		// フォーム全体のエラー状態を管理するフラグ
		const errors = new Map();		// id: [msg, focusBody]
		let validations = {};

		// 2) 入力時（input）／フォーカスアウト時（blur）にバリデート
		function validateObtainDate() {
			const val = obtainDateInput.value.trim();
			if (val !== '' && !validateDatetime(val)) {
				// 不正データ
				msg = '不正な日時です。「YYYY/MM/DD hh:mm:ss」の形式で入力してください。（時刻は省略可能）';
				showWarning(obtainDateInput, msg);
				errors.set('obtainDate', [msg, obtainDateInput]);
			} else {
				// 正常
				showWarning(obtainDateInput, '');
				errors.delete('obtainDate');
			}
		}

		validations['obtainDate'] = {
			validator: validateObtainDate, targets: [obtainDateInput]
		};

		function validateTotal() {
			const total = parseInt(totalInput.value.trim());
			const subtotal = parseInt(subtotalInput.value.trim());
			const tax = parseInt(taxInput.value.trim());
			const extraFee = parseInt(extraFeeInput.value.trim());

			if (!isNaN(total) && !isNaN(subtotal) && !isNaN(tax)
				&& total != subtotal + tax + (extraFee || 0)) {
				// 不正データ
				msg = '(支払金額)が(税抜合計 + 税額 + 送料等)と一致しません。';
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
		const form = document.querySelector('form');
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
			}
		});

		// ページロード後に一度チェックを走らせておく
		validate();
	});
})();