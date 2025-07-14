// 関数のスコープ外で正規表現を定義（前回の最適化を適用）
const REGEX_JP_FULL = /(\d{4})年(?:(\d{1,2})月(?:(\d{1,2})日(?: (\d{1,2})時(?:(\d{1,2})分(?:(\d{1,2})秒)?)?)?)?)?/i;
const REGEX_SLASH_HYPHEN_FULL = /(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?/i;
const REGEX_YMD = /(\d{4})[/-](\d{1,2})[/-](\d{1,2})/i;
const REGEX_YM = /(\d{4})(?:年|[/]|[-])(\d{1,2})/i; // '年' も考慮
const REGEX_YEAR_ONLY = /^(\d{4})(?:年)?$/i;

// 新しくタイムゾーンオフセットを含む正規表現を追加
// 例: +09:00, -05:00, Z (UTC)
const REGEX_TIME_WITH_OFFSET = /(\d{4})[/-](\d{1,2})[/-](\d{1,2})[ T](\d{1,2}):(\d{1,2})(?::(\d{1,2}))?([Zz]|[-+](\d{2}):?(\d{2}))?/i;

/**
 * 様々な書式の日時文字列をパースし、Dateオブジェクトを返します。
 * 日時文字列は、年、月、日、時、分、秒の各要素が省略されていても対応します。
 * また、一部のタイムゾーンオフセット形式にも対応します。
 *
 * @param {string} dateTimeString パースする日時文字列。
 * @returns {Date | null} パースされたDateオブジェクト、またはパースできなかった場合はnull。
 */
function parseFlexibleDateTime(dateTimeString) {
    if (!dateTimeString || typeof dateTimeString !== 'string') {
        return null;
    }

    let year = 0, month = 0, day = 1, hour = 0, minute = 0, second = 0;

    // 1. タイムゾーンオフセットを含む可能性のある書式を最優先で試す
    // この形式はDate.parse()が比較的うまく処理できるため、最初に試します。
    const timeWithOffsetMatch = dateTimeString.match(REGEX_TIME_WITH_OFFSET);
    if (timeWithOffsetMatch) {
        // オフセットがある場合は、Dateコンストラクタが自動的にUTCに変換してくれる
        const parsedDateWithOffset = new Date(dateTimeString);
        if (!isNaN(parsedDateWithOffset.getTime())) {
            return parsedDateWithOffset;
        }
    }

    // 2. 日本語の書式 (年、月、日、時、分、秒)
    const jpFullMatch = dateTimeString.match(REGEX_JP_FULL);
    if (jpFullMatch) {
        year = parseInt(jpFullMatch[1]);
        month = jpFullMatch[2] ? parseInt(jpFullMatch[2]) - 1 : 0; // 月は0-indexed
        day = jpFullMatch[3] ? parseInt(jpFullMatch[3]) : 1;
        hour = jpFullMatch[4] ? parseInt(jpFullMatch[4]) : 0;
        minute = jpFullMatch[5] ? parseInt(jpFullMatch[5]) : 0;
        second = jpFullMatch[6] ? parseInt(jpFullMatch[6]) : 0;
        return new Date(year, month, day, hour, minute, second);
    }

    // 3. スラッシュまたはハイフン区切りの書式 (年/月/日 または 年-月-日)
    // ここはタイムゾーンオフセットがない形式を想定
    const slashHyphenFullMatch = dateTimeString.match(REGEX_SLASH_HYPHEN_FULL);
    if (slashHyphenFullMatch) {
        year = parseInt(slashHyphenFullMatch[1]);
        month = parseInt(slashHyphenFullMatch[2]) - 1;
        day = parseInt(slashHyphenFullMatch[3]);
        hour = slashHyphenFullMatch[4] ? parseInt(slashHyphenFullMatch[4]) : 0;
        minute = slashHyphenFullMatch[5] ? parseInt(slashHyphenFullMatch[5]) : 0;
        second = slashHyphenFullMatch[6] ? parseInt(slashHyphenFullMatch[6]) : 0;
        return new Date(year, month, day, hour, minute, second);
    }

    // 4. 年月日のみの書式 (スラッシュまたはハイフン区切り)
    const ymdMatch = dateTimeString.match(REGEX_YMD);
    if (ymdMatch) {
        year = parseInt(ymdMatch[1]);
        month = parseInt(ymdMatch[2]) - 1;
        day = parseInt(ymdMatch[3]);
        return new Date(year, month, day);
    }

    // 5. 年月のみの書式 (日本語、スラッシュ、ハイフン)
    const ymMatch = dateTimeString.match(REGEX_YM);
    if (ymMatch) {
        year = parseInt(ymMatch[1]);
        month = parseInt(ymMatch[2]) - 1;
        return new Date(year, month, 1);
    }

    // 6. 年のみの書式 (日本語、数値のみ)
    const yearOnlyMatch = dateTimeString.match(REGEX_YEAR_ONLY);
    if (yearOnlyMatch) {
        year = parseInt(yearOnlyMatch[1]);
        return new Date(year, 0, 1);
    }

    // 7. その他のISO 8601互換形式（Date.parseに任せる）
    // 例: "YYYY-MM-DDTHH:MM:SSZ", "YYYY-MM-DDTHH:MM:SS+HH:MM" など
    // ここに到達する文字列は、前の`REGEX_TIME_WITH_OFFSET`で処理されなかったが、
    // Date.parse()が理解できる形式である可能性のある文字列です。
    const parsedDate = new Date(dateTimeString);
    if (!isNaN(parsedDate.getTime())) {
        return parsedDate;
    }

    return null;
}

// テスト
console.log("--- テスト開始 ---");

// 完全な日時文字列
console.log(`2023年01月23日 14時35分45秒:\n ${parseFlexibleDateTime("2023年01月23日 14時35分45秒")}`);
console.log(`2023/01/23 14:35:45:\n ${parseFlexibleDateTime("2023/01/23 14:35:45")}`);
console.log(`2023-01-23 14:35:45:\n ${parseFlexibleDateTime("2023-01-23 14:35:45")}`);

// 分まで
console.log(`2023年01月23日 14時35分:\n ${parseFlexibleDateTime("2023年01月23日 14時35分")}`);
console.log(`2023/01/23 14:35:\n ${parseFlexibleDateTime("2023/01/23 14:35")}`);
console.log(`2023-01-23 14:35:\n ${parseFlexibleDateTime("2023-01-23 14:35")}`);

// 日まで
console.log(`2023年01月23日:\n ${parseFlexibleDateTime("2023年01月23日")}`);
console.log(`2023/01/23:\n ${parseFlexibleDateTime("2023/01/23")}`);
console.log(`2023-01-23:\n ${parseFlexibleDateTime("2023-01-23")}`);

// 月まで
console.log(`2023年01月:\n ${parseFlexibleDateTime("2023年01月")}`);
console.log(`2023/01:\n ${parseFlexibleDateTime("2023/01")}`);
console.log(`2023-01:\n ${parseFlexibleDateTime("2023-01")}`);

// 年のみ
console.log(`2023年:\n ${parseFlexibleDateTime("2023年")}`);
console.log(`2023:\n ${parseFlexibleDateTime("2023")}`);

// 不正な入力
console.log(`不正な文字列:\n ${parseFlexibleDateTime("不正な文字列")}`);
console.log(`null:\n ${parseFlexibleDateTime(null)}`);
console.log(`undefined:\n ${parseFlexibleDateTime(undefined)}`);
console.log(`空文字列:\n ${parseFlexibleDateTime("")}`);

console.log("--- タイムゾーンを含む書式テスト ---");

// UTC (Z)
console.log(`2023-01-23T14:35:45Z (UTC): ${parseFlexibleDateTime("2023-01-23T14:35:45Z")}`);
// オフセット
console.log(`2023-01-23T14:35:45+09:00 (JST): ${parseFlexibleDateTime("2023-01-23T14:35:45+09:00")}`);
console.log(`2023/01/23 14:35:45-0500 (EST): ${parseFlexibleDateTime("2023/01/23 14:35:45-0500")}`); // スラッシュ形式でオフセット
console.log(`2023-01-23 14:35:45+0000 (GMT): ${parseFlexibleDateTime("2023-01-23 14:35:45+0000")}`); // スペース区切り


console.log("--- テスト終了 ---");