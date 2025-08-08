/**
 * @module fuzzy-datetime
 * @description
 * 日付・日時文字列を、設定可能な精度とゼロパディングで解析・正規化するためのライブラリ。
 */

import { TZ_MAP } from './tz.js';

// --- 定数群 ---

// --- 正規表現パターン ---
const dateTimeReg = new RegExp(
	"^(?<year>\\d{4})" +
	"(?:" +
		"(?<sep1>[/.-])(?<month>\\d{1,2})" +
		"(?:" +
			"(?<sep2>[/.-])(?<day>\\d{1,2})" +
			"(?:" +
				"[ T](?<hour>\\d{1,2})" +
				"(?:" +
					"(?<sep3>[:.-])(?<minute>\\d{1,2})" +
					"(?:" +
						"(?<sep4>[:.-])(?<second>\\d{1,2})" +
					")?" +
				")?" +
				"(?:" +
					"\\s?(?<tz>[a-zA-Z_]+|(?:UTC)?(?<sign>[+-])(?<offset>(?<hours>\\d{1,2}):(?<minutes>\\d{1,2})|(?<plain_offset>\\d{1,4}))|[a-zA-Z]+/[a-zA-Z_]+)" +
				")?" +
			")?" +
		")?" +
	")?$"
)
const dateReg = /^(?<year>\d{4})(?:(?<sep1>[-\/.])(?<month>\d{1,2})(?:(?<sep2>[-\/.])(?<day>\d{1,2}))?)?$/;

const dateTimePrecisionOrder = ['year', 'month', 'day', 'hour', 'minute', 'second'];
const datePrecisionOrder = ['year', 'month', 'day'];

// --- カスタムエラークラス ---

/**
 * 日時関連のエラーを表す基底カスタムエラークラス。
 * @param {string} message - エラーメッセージ。
 * @param {string} [code] - エラーを識別するためのコード。
 * @param {object} [details] - エラーに関する追加情報。
 */
export class DateTimeError extends Error {
	constructor(message, code = 'UNKNOWN_ERROR', details = {}) {
		super(message);
		this.name = 'DateTimeError';
		this.code = code;
		this.details = details;
	}
}

/**
 * 書式が不正な場合のエラー。
 */
export class InvalidFormatError extends DateTimeError {
	constructor(message, details = {}) {
		super(message, 'INVALID_FORMAT', details);
		this.name = 'InvalidFormatError';
	}
}

/**
 * 値が範囲外の場合のエラー。
 */
export class InvalidValueError extends DateTimeError {
	constructor(message, details = {}) {
		super(message, 'INVALID_VALUE', details);
		this.name = 'InvalidValueError';
	}
}


/**
 * 精度が不足している場合のエラー。
 */
export class PrecisionError extends DateTimeError {
	constructor(message, details = {}) {
		super(message, 'PRECISION_NOT_MET', details);
		this.name = 'PrecisionError';
	}
}

/**
 * タイムゾーンが不正な場合のエラー。
 */
export class InvalidTimezoneError extends DateTimeError {
	constructor(message, details = {}) {
		super(message, 'INVALID_TIMEZONE', details);
		this.name = 'InvalidTimezoneError';
	}
}


// --- 主要関数群 ---

/**
 * 日時文字列の形式と値の妥当性を検証します。
 *
 * @param {string} s - 検証する日時文字列。
 * @param {Object} [options={}] - オプション。
 * @param {('year'|'month'|'day'|'hour'|'minute'|'second')} [options.requiredPrecision='year'] - 必要な最小精度。
 * @returns {boolean} 日時文字列が有効な場合は`true`、そうでない場合は`false`を返します。
 */
export function validateDateTimeStr(s, options = {}) {
	try {
		matchDateTime(s, options);
		return true;
	} catch (e) {
		if (e instanceof DateTimeError)
			return false;
		throw e;
	}
}

/**
 * 日付文字列の形式と値の妥当性を検証します。
 *
 * @param {string} s - 検証する日付文字列。
 * @param {Object} [options={}] - オプション。
 * @param {('year'|'month'|'day')} [options.requiredPrecision='year'] - 必要な最小精度。
 * @returns {boolean} 有効ならtrue、無効ならfalse。
 */
export function validateDateStr(s, options = {}) {
	try {
		matchDate(s, options);
		return true;
	} catch (e) {
		if (e instanceof DateTimeError)
			return false;
		throw e;
	}
}

/**
 * 日付時刻文字列をDateオブジェクトに解析します。
 * @param {string} s - 入力となる日付時刻文字列。
 * @param {Object} [options={}] - オプション。
 * @param {('year'|'month'|'day'|'hour'|'minute'|'second')} [options.requiredPrecision='year'] - 必要な最小精度。
 * @param {string} [options.defTz='UTC'] - デフォルトのタイムゾーン。
 * @returns {Date} 解析されたDateオブジェクト。
 * @throws {DateTimeError}
 */
export function parseDateTime(s, options = {}) {
	const { defTz = 'UTC', requiredPrecision = 'year', acceptMixedSep = true } = options;
	const { groups, parts, tz } = matchDateTime(s, { requiredPrecision, acceptMixedSep });

	const utcMillis = Date.UTC(
		parts.year,
		parts.month - 1,	// Date.UTC の month は 0–11
		parts.day,
		parts.hour,
		parts.minute,
		parts.second,
	) - tz.offsetMins * 60000;
	return new Date(utcMillis);
}

/**
 * 日付文字列をDateオブジェクトに解析します。
 *
 * @param {string} s - 日付文字列。
 * @param {Object} [options={}] - オプション。
 * @param {('year'|'month'|'day')} [options.requiredPrecision='year'] - 必要な最小精度。
 * @returns {Date}
 * @throws {DateTimeError}
 */
export function parseDate(s, options = {}) {
	const { requiredPrecision = 'year', acceptMixedSep = true } = options;
	const { parts } = matchDate(s, { requiredPrecision, acceptMixedSep });

	// 時刻情報がないのでローカルタイムの午前0時として扱う
	const utcMillis = Date.UTC(parts.year, parts.month - 1, parts.day);
	return new Date(utcMillis);
}

/**
 * 日付時刻文字列を一貫した形式に正規化します。
 * @param {string} s - 入力となる日付時刻文字列。
 * @param {Object} [options={}] - オプション
 * @param {boolean} [options.zeroPad=true] - 月、日、時、分、秒をゼロパディングするかどうか。
 * @param {('year'|'month'|'day'|'hour'|'minute'|'second'|null)} [options.minPrecision=null] - 出力が保証される最小精度。nullの場合、入力の精度を維持。
 * @param {string} [options.dateSep='/'] - 日付の区切り文字。
 * @param {string} [options.timeSep=':'] - 時刻の区切り文字。
 * @param {boolean} [options.forceTz=false] - タイムゾーン情報がない場合でもデフォルトTZを付与するか。
 * @param {string} [options.defTz='UTC'] -入力文字列にタイムゾーンが含まれていない場合に試用されるデフォルトタイムゾーン。
 * @param {('year'|'month'|'day'|'hour'|'minute'|'second')} [options.requiredPrecision='year'] - 入力文字列に要求される最小精度を指定します。nullの場合、精度の検証は行われません。
 * @param {boolean} [options.acceptMixedSep=true] - 日付と時刻の区切り文字が混在している場合に許可するかどうか。
 * @returns {string} 正規化された日付時刻文字列。
 * @throws {DateTimeError}
 */
export function normalizeDateTime(s, options = {}) {
	const {
		zeroPad = true,
		minPrecision = null,
		dateSep = '/',
		timeSep = ':',
		forceTz = false,
		defTz = 'UTC',
		requiredPrecision = 'year',
		acceptMixedSep = true,
	} = options;

	const { groups: g, parts, precisionIndex: inPrecisionIdx, tz } = matchDateTime(s, { requiredPrecision, acceptMixedSep });

	// 出力すべき日時精度の決定
	let outPrecisionIdx = inPrecisionIdx;
	if (minPrecision != null) {
		const minPrecisionIdx = dateTimePrecisionOrder.indexOf(minPrecision);
		if (minPrecisionIdx === -1)
			throw new InvalidValueError(`Unknown minPrecision: ${minPrecision}`, { input: s, minPrecision });
		if (outPrecisionIdx < minPrecisionIdx)
			outPrecisionIdx = minPrecisionIdx;
	}

	// 文字列組み立て
	let out = zeroPad ? _pad(parts.year, 4) : String(parts.year);
	if (outPrecisionIdx >= 1)
		out += dateSep + (zeroPad ? _pad(parts.month) : parts.month);
	if (outPrecisionIdx >= 2)
		out += dateSep + (zeroPad ? _pad(parts.day) : parts.day);
	if (outPrecisionIdx >= 3)
		out += ' ' + (zeroPad ? _pad(parts.hour) : parts.hour);
	if (outPrecisionIdx >= 4)
		out += timeSep + (zeroPad ? _pad(parts.minute) : parts.minute);
	if (outPrecisionIdx >= 5)
		out += timeSep + (zeroPad ? _pad(parts.second) : parts.second);

	// タイムゾーン
	if (tz)
		out += ' ' + tz.label;

	return out;
}

/**
 * 日付文字列を一貫した形式に正規化します。
 *
 * @param {string} s - 入力日付文字列。
 * @param {Object} [options={}] - オプション
 * @param {boolean} [options.zeroPad=true] - 月、日、時、分、秒をゼロパディングするかどうか。
 * @param {('year'|'month'|'day'|null)} [options.minPrecision=null] - 出力が保証される精度を指定します。nullの場合、入力の精度が維持されます。
 * @param {string} [options.dateSep='/'] - 日付部分の区切り文字。
 * @param {('year'|'month'|'day')} [options.requiredPrecision='year'] - 入力文字列に要求される最小精度を指定します。nullの場合、精度の検証は行われません。
 * @param {boolean} [options.acceptMixedSep=true] - 日付と時刻の区切り文字が混在している場合に許可するかどうか。
 * @returns {string} 正規化された日付文字列。
 * @throws {Error}
 */
export function normalizeDate(s, options = {}) {
	const {
		zeroPad = true,
		minPrecision = null,
		sep = '/',
		requiredPrecision = 'year',
		acceptMixedSep = true,
	} = options;
	const { groups: g, parts, precisionIndex: inPrecisionIdx } = matchDate(s, { requiredPrecision, acceptMixedSep });

	// 出力すべき日付精度の決定
	let outPrecisionIdx = inPrecisionIdx;
	if (minPrecision != null) {
		const minPrecisionIdx = datePrecisionOrder.indexOf(minPrecision);
		if (minPrecisionIdx === -1)
			throw new InvalidValueError(`Unknown minPrecision: ${minPrecision}`, { input: s, minPrecision });
		if (outPrecisionIdx < minPrecisionIdx)
			outPrecisionIdx = minPrecisionIdx;
	}

	// 文字列組み立て
	let out = zeroPad ? _pad(parts.year, 4) : String(parts.year);
	if (outPrecisionIdx >= 1)
		out += sep + (zeroPad ? _pad(parts.month) : parts.month);
	if (outPrecisionIdx >= 2)
		out += sep + (zeroPad ? _pad(parts.day) : parts.day);

	return out;
}

// --- 内部関数 ---

// --- ヘルパー関数 ---

/**
 * 数値をゼロパディングして文字列に変換します。
 * @param {number} val - ゼロパディングする数値。
 * @param {number} [len=2] - パディング後の文字列の最小長。
 * @returns {string} ゼロパディングされた文字列。
 */
function _pad(val, len = 2) {
	return String(val).padStart(len, '0');
}

/**
 * 正規表現マッチ結果を検証し、数値として解析して返す。
 * @param {string} s - 入力文字列
 * @returns {Object} グループオブジェクトと数値パーツ
 * @throws {Error} 不正なフォーマットや範囲外の値
 */
function matchDateTime(s, options = {}) {
	const {
		requiredPrecision = 'year',
		acceptMixedSep = true,
	} = options;

	const m = s.match(dateTimeReg);
	if (!m || !m.groups)
		throw new InvalidFormatError(`Invalid datetime format: "${s}"`, { input: s });
	const g = m.groups;

	// 入力の日時精度の特定
	let inPrecisionIdx = dateTimePrecisionOrder.length - 1;
	for (let i = 1; i < dateTimePrecisionOrder.length; i++) {
		if (g[dateTimePrecisionOrder[i]] == null) {
			inPrecisionIdx = i - 1;
			break;
		}
	}

	// 要求精度に対する検証
	if (requiredPrecision && requiredPrecision != 'year') {
		const requiredPrecisionIdx = dateTimePrecisionOrder.indexOf(requiredPrecision);
		if (requiredPrecisionIdx === -1)
			throw new InvalidValueError(`Unknown requiredPrecision: ${requiredPrecision}`, { input: s, requiredPrecision });
		if (inPrecisionIdx < requiredPrecisionIdx)
			throw new PrecisionError(`Precision not met (${requiredPrecision}) for "${s}"`, { input: s, requiredPrecision });
	}

	// 区切り記号の検証
	if (!acceptMixedSep) {
		if (g.sep1 && g.sep2 && g.sep1 !== g.sep2)
			throw new InvalidFormatError(`Mixed date separators in "${s}"`, { input: s, sep1: g.sep1, sep2: g.sep2 });
		if (g.sep3 && g.sep4 && g.sep3 !== g.sep4)
			throw new InvalidFormatError(`Mixed time separators in "${s}"`, { input: s, sep3: g.sep3, sep4: g.sep4 });
	}

	// 数値に変換
	const parts = {
		year: parseInt(g.year, 10),
		month: g.month ? +g.month : 1,
		day: g.day ? +g.day : 1,
		hour: g.hour ? +g.hour : 0,
		minute: g.minute ? +g.minute : 0,
		second: g.second ? +g.second : 0
	};

	// 値の検証
	if (parts.month < 1 || parts.month > 12)
		throw new InvalidValueError(`Month out of range: ${parts.month}`, { input: s, month: parts.month });
	const daysInMonth = new Date(parts.year, parts.month, 0).getDate();
	if (parts.day < 1 || parts.day > daysInMonth)
		throw new InvalidValueError(`Day out of range: ${parts.day}`, { input: s, day: parts.day });
	if (parts.hour < 0 || parts.hour > 23)
		throw new InvalidValueError(`Hour out of range: ${parts.hour}`, { input: s, hour: parts.hour });
	if (parts.minute < 0 || parts.minute > 59)
		throw new InvalidValueError(`Minute out of range: ${parts.minute}`, { input: s, minute: parts.minute });
	if (parts.second < 0 || parts.second > 59)
		throw new InvalidValueError(`Second out of range: ${parts.second}`, { input: s, second: parts.second });

	// タイムゾーンの検証
	let tz = null;
	if (g.tz) {
		try {
			tz = parseTz(g);
		} catch (e) {
			if (e instanceof InvalidFormatError) {
				throw new InvalidTimezoneError(`Invalid timezone format: "${g.tz}"`, { input: s, tz: g.tz });
			}
			throw e;
		}
	}

	return {
		groups: g,
		parts,
		precisionIndex: inPrecisionIdx,
		precision: dateTimePrecisionOrder[inPrecisionIdx],
		tz,
	};
}


function matchDate(s, options = {}) {
	const {
		requiredPrecision = 'year',
		acceptMixedSep = true,
	} = options;

	const m = s.match(dateReg);
	if (!m || !m.groups)
		throw new InvalidFormatError(`Invalid date format: "${s}"`, { input: s });
	const g = m.groups;

	// 入力の日時精度の特定
	let inPrecisionIdx = datePrecisionOrder.length - 1;
	for (let i = 1; i < datePrecisionOrder.length; i++) {
		if (g[datePrecisionOrder[i]] == null) {
			inPrecisionIdx = i - 1;
			break;
		}
	}

	// 要求精度に対する検証
	if (requiredPrecision && requiredPrecision != 'year') {
		const requiredPrecisionIdx = datePrecisionOrder.indexOf(requiredPrecision);
		if (requiredPrecisionIdx === -1)
			throw new InvalidValueError(`Unknown requiredPrecision: ${requiredPrecision}`, { input: s, requiredPrecision });
		if (inPrecisionIdx < requiredPrecisionIdx)
			throw new PrecisionError(`Required precision '${requiredPrecision}' not met by input: "${s}"`, { input: s, requiredPrecision });
	}


	// 区切り記号の検証
	if (!acceptMixedSep && g.sep1 && g.sep2 && g.sep1 !== g.sep2)
		throw new InvalidFormatError(`Mixed date separators are not allowed: "${s}"`, { input: s, sep1: g.sep1, sep2: g.sep2 });

	// 数値に変換
	const parts = {
		year: parseInt(g.year, 10),
		month: g.month ? parseInt(g.month, 10) : 1,
		day: g.day ? parseInt(g.day, 10) : 1,
	};

	// 値の検証
	if (parts.month < 1 || parts.month > 12)
		throw new InvalidValueError(`Invalid month value ${parts.month} in "${s}"`, { input: s, month: parts.month });
	const daysInMonth = new Date(parts.year, parts.month, 0).getDate();
	if (parts.day < 1 || parts.day > daysInMonth)
		throw new InvalidValueError(`Invalid day value ${parts.day} in "${s}"`, { input: s, day: parts.day });

	return { groups: g, parts, precisionIndex: inPrecisionIdx, precision: datePrecisionOrder[inPrecisionIdx] };
}

/**
 * テキストからのタイムゾーン表記を解析し、標準化されたオフセット文字列と分単位のオフセットを返します。
 * @param {string} s - 生のタイムゾーン（例: 'Z', 'UTC', 'JST', '+09:00' など）
 * @param {string} [options.defTz='UTC'] - デフォルトのタイムゾーン
 * @returns {Object} タイムゾーンオフセットの文字列と分単位のオフセット
 * @throws {Error} 不明なフォーマット
 */
function parseTz(g, options = {}) {
	const { defTz = 'UTC', forceTz = false } = options;

	let tz = (g.tz || defTz).toUpperCase();
	if (tz === 'Z') {
		tz = 'UTC';
		return { type: 'z', label: tz, ... TZ_MAP[tz]};
	}
	if (TZ_MAP[tz])
		return { type: 'abbr', label: tz, ...TZ_MAP[tz] };

	// +HH:MM／-HHMM 形式のパース
	if (g.offset) {
		let h, mm;
		if (g.plain_offset) {
			// HHMM 形式
			let po = g.plain_offset;
			switch (po.length) {
			case 1:	// H
			case 2:	// HH
				h = po;
				mm = '0';
				break;
			case 3: // HMM
				h = po.slice(0, 1);
				mm = po.slice(1, 3);
				break;
			case 4: // HHMM
				h = po.slice(0, 2);
				mm = po.slice(2, 4);
				break;
			}
		} else {
			h = g.hours;
			mm = g.minutes;
		}
		const sign = g.sign;
		const offsetStr = `${sign}${h.padStart(2, '0')}:${mm.padStart(2, '0')}`
		const offsetMins = parseInt(h, 10) * 60 + parseInt(mm, 10);

		return {
			type: 'offset',
			label: offsetStr,
			offsetStr,
			offsetMins: sign == '-' ? -offsetMins : offsetMins,
		};
	}

	throw new InvalidFormatError(`Unknown timezone format: "${s}"`, { input: s });
}