/* static/js/book_form.js */

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

		// 入力時（input）／フォーカスアウト時（blur）にバリデート
		function validatePublicationDate() {
			const val = publicationDateInput.value.trim();
			if (val !== '' && !validateDatetime(val)) {
				// 不正データ
				msg = '不正な日時です。「YYYY/MM/DD hh:mm:ss」の形式で入力してください。（時刻は省略可能）';
				showWarning(publicationDateInput, msg);
				errors.set('publicationDate', [msg, publicationDateInput]);
			} else {
				// 正常
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