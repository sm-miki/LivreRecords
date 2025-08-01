
/**
 * タイムゾーンの略語、オフセット文字列
 、およびオフセット分数（分単位）のマッピング。
 * @type {Object.<string, {offsetStr: string, offsetMins: number}>}
 */
export const TZ_MAP = {
	UTC: { offsetStr: '+00:00', offsetMins: 0 }, // 協定世界時
	GMT: { offsetStr: '+00:00', offsetMins: 0 }, // グリニッジ標準時

	// 北米
	EST: { offsetStr: '-05:00', offsetMins: -300 }, // 東部標準時
	EDT: { offsetStr: '-04:00', offsetMins: -240 }, // 東部夏時間
	CST: { offsetStr: '-06:00', offsetMins: -360 }, // 中央標準時
	CDT: { offsetStr: '-05:00', offsetMins: -300 }, // 中央夏時間
	MST: { offsetStr: '-07:00', offsetMins: -420 }, // 山岳部標準時
	MDT: { offsetStr: '-06:00', offsetMins: -360 }, // 山岳部夏時間
	PST: { offsetStr: '-08:00', offsetMins: -480 }, // 太平洋標準時
	PDT: { offsetStr: '-07:00', offsetMins: -420 }, // 太平洋夏時間
	AKST: { offsetStr: '-09:00', offsetMins: -540 }, // アラスカ標準時
	AKDT: { offsetStr: '-08:00', offsetMins: -480 }, // アラスカ夏時間
	HST: { offsetStr: '-10:00', offsetMins: -600 }, // ハワイ標準時 (夏時間なし)

	// ヨーロッパ
	BST: { offsetStr: '+01:00', offsetMins: 60 }, // 英国夏時間 (イギリス)
	CET: { offsetStr: '+01:00', offsetMins: 60 }, // 中央ヨーロッパ時間
	CEST: { offsetStr: '+02:00', offsetMins: 120 }, // 中央ヨーロッパ夏時間
	EET: { offsetStr: '+02:00', offsetMins: 120 }, // 東ヨーロッパ時間
	EEST: { offsetStr: '+03:00', offsetMins: 180 }, // 東ヨーロッパ夏時間
	WET: { offsetStr: '+00:00', offsetMins: 0 }, // 西ヨーロッパ時間
	WEST: { offsetStr: '+01:00', offsetMins: 60 }, // 西ヨーロッパ夏時間

	// アジア
	JST: { offsetStr: '+09:00', offsetMins: 540 }, // 日本標準時
	IST: { offsetStr: '+05:30', offsetMins: 330 }, // インド標準時
	KST: { offsetStr: '+09:00', offsetMins: 540 }, // 韓国標準時
	SGT: { offsetStr: '+08:00', offsetMins: 480 }, // シンガポール標準時
	MYT: { offsetStr: '+08:00', offsetMins: 480 }, // マレーシア時間
	ICT: { offsetStr: '+07:00', offsetMins: 420 }, // インドシナ時間 (タイ、ベトナムなど)
	WIB: { offsetStr: '+07:00', offsetMins: 420 }, // 西インドネシア時間
	WITA: { offsetStr: '+08:00', offsetMins: 480 }, // 中部インドネシア時間
	WIT: { offsetStr: '+09:00', offsetMins: 540 }, // 東インドネシア時間

	// オーストラリア
	AEST: { offsetStr: '+10:00', offsetMins: 600 }, // オーストラリア東部標準時
	AEDT: { offsetStr: '+11:00', offsetMins: 660 }, // オーストラリア東部夏時間
	ACST: { offsetStr: '+09:30', offsetMins: 570 }, // オーストラリア中央標準時
	ACDT: { offsetStr: '+10:30', offsetMins: 630 }, // オーストラリア中央夏時間
	AWST: { offsetStr: '+08:00', offsetMins: 480 }, // オーストラリア西部標準時 (夏時間なし)

	// 南米
	BRT: { offsetStr: '-03:00', offsetMins: -180 }, // ブラジル時間
	ART: { offsetStr: '-03:00', offsetMins: -180 }, // アルゼンチン時間
	CLT: { offsetStr: '-04:00', offsetMins: -240 }, // チリ標準時
	CLST: { offsetStr: '-03:00', offsetMins: -180 }, // チリ夏時間

	// アフリカ
	SAST: { offsetStr: '+02:00', offsetMins: 120 }, // 南アフリカ標準時
	CAT: { offsetStr: '+02:00', offsetMins: 120 }, // 中央アフリカ時間
	EAT: { offsetStr: '+03:00', offsetMins: 180 }, // 東アフリカ時間

	// その他
	NZST: { offsetStr: '+12:00', offsetMins: 720 }, // ニュージーランド標準時
	NZDT: { offsetStr: '+13:00', offsetMins: 780 }, // ニュージーランド夏時間
};
