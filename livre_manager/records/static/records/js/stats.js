function openTab(evt, tabName) {
	var i, tabcontent, tablinks;
	tabcontent = document.getElementsByClassName("tab-content");

 	// すべてのタブコンテンツを非表示にする
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].style.display = "none";
	}
	tablinks = document.getElementsByClassName("tab-button");
	for (i = 0; i < tablinks.length; i++) {
		tablinks[i].className = tablinks[i].className.replace(" active", "");
	}
	document.getElementById(tabName).style.display = "block";
	evt.currentTarget.className += " active";

	// URLのハッシュを更新 (ブラウザの履歴には追加しない)
 	if (evt.isTrusted) {
 		if (history.replaceState) {
 			history.replaceState(null, null, '#' + tabName);
 		} else {
 			location.hash = '#' + tabName;
 		}
 	}
}

document.addEventListener('DOMContentLoaded', function() {
	// URLのハッシュに基づいて表示するタブを決定する
	const hash = window.location.hash.substring(1);
	let buttonToClick = null;

	if (hash) {
		// ハッシュに一致するdata-tab属性を持つボタンを探す
		buttonToClick = document.querySelector(`.tab-button[data-tab="${hash}"]`);
	}

	// 該当するボタンが見つからない場合、デフォルトのタブを開く
	if (!buttonToClick) {
		buttonToClick = document.getElementById('defaultOpen');
	}

	// ボタンをクリックしてタブを開く
	if (buttonToClick) {
		buttonToClick.click();
	}
});