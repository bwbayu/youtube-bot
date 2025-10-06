import unicodedata
import re
from bs4 import BeautifulSoup

# Mapping untuk mengganti karakter mirip huruf/angka (visual clones)
CHARACTER_MAP = {
    # Unicode fancy to normal
    '𝐀': 'A', '𝐁': 'B', '𝐂': 'C', '𝐃': 'D', '𝐄': 'E', '𝐅': 'F', '𝐆': 'G',
    '𝐇': 'H', '𝐈': 'I', '𝐉': 'J', '𝐊': 'K', '𝐋': 'L', '𝐌': 'M', '𝐍': 'N',
    '𝐎': 'O', '𝐏': 'P', '𝐐': 'Q', '𝐑': 'R', '𝐒': 'S', '𝐓': 'T', '𝐔': 'U',
    '𝐕': 'V', '𝐖': 'W', '𝐗': 'X', '𝐘': 'Y', '𝐙': 'Z',
    '𝐚': 'a', '𝐛': 'b', '𝐜': 'c', '𝐝': 'd', '𝐞': 'e', '𝐟': 'f', '𝐠': 'g',
    '𝐡': 'h', '𝐢': 'i', '𝐣': 'j', '𝐤': 'k', '𝐥': 'l', '𝐦': 'm', '𝐧': 'n',
    '𝐨': 'o', '𝐩': 'p', '𝐪': 'q', '𝐫': 'r', '𝐬': 's', '𝐭': 't', '𝐮': 'u',
    '𝐯': 'v', '𝐰': 'w', '𝐱': 'x', '𝐲': 'y', '𝐳': 'z',
    
    # Gothic/Fraktur
    '𝔄': 'A', '𝔅': 'B', 'ℭ': 'C', '𝔇': 'D', '𝔈': 'E', '𝔉': 'F', '𝔊': 'G',
    '𝔍': 'J', '𝔎': 'K', '𝔏': 'L', '𝔐': 'M', '𝔑': 'N', '𝔒': 'O', '𝔓': 'P',
    '𝔔': 'Q', 'ℜ': 'R', '𝔖': 'S', '𝔗': 'T', '𝔘': 'U', '𝔙': 'V', '𝔚': 'W',
    '𝔛': 'X', '𝔜': 'Y', '𝔞': 'a', '𝔟': 'b', '𝔠': 'c', '𝔡': 'd',
    '𝔢': 'e', '𝔣': 'f', '𝔤': 'g', '𝔥': 'h', '𝔦': 'i', '𝔧': 'j',
    '𝔨': 'k', '𝔩': 'l', '𝔪': 'm', '𝔫': 'n', '𝔬': 'o', '𝔭': 'p',
    '𝔮': 'q', '𝔯': 'r', '𝔰': 's', '𝔱': 't', '𝔲': 'u', '𝔳': 'v',
    '𝔴': 'w', '𝔵': 'x', '𝔶': 'y', '𝔷': 'z',

    # Emoji angka ke angka
    '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
    '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9',

    # Unicode angka gaya
    '𝟎': '0', '𝟏': '1', '𝟐': '2', '𝟑': '3', '𝟒': '4',
    '𝟓': '5', '𝟔': '6', '𝟕': '7', '𝟖': '8', '𝟗': '9',

    # Bulatan/simbol angka
    '❶': '1', '❷': '2', '❸': '3', '❹': '4', '❺': '5',
    '❻': '6', '❼': '7', '❽': '8', '❾': '9', '❿': '10',
    
    # Simbol huruf
    'ⓐ': 'a', 'ⓑ': 'b', 'ⓒ': 'c', 'ⓓ': 'd', 'ⓔ': 'e', 'ⓕ': 'f', 'ⓖ': 'g',
    'ⓗ': 'h', 'ⓘ': 'i', 'ⓙ': 'j', 'ⓚ': 'k', 'ⓛ': 'l', 'ⓜ': 'm', 'ⓝ': 'n',
    'ⓞ': 'o', 'ⓟ': 'p', 'ⓠ': 'q', 'ⓡ': 'r', 'ⓢ': 's', 'ⓣ': 't', 'ⓤ': 'u',
    'ⓥ': 'v', 'ⓦ': 'w', 'ⓧ': 'x', 'ⓨ': 'y', 'ⓩ': 'z',
    
    # Simbol aneh
    'ᗪ': 'D', 'ᗩ': 'A', 'ᒪ': 'L', 'ᑭ': 'P', 'ᖇ': 'R', 'ᗷ': 'B', 'ᑕ': 'C', 'ᗷ': 'B',

    '🅰️': 'A', '🅱️': 'B', '🅾️': 'O', '🆎': 'AB', '🆑': 'CL', '🆒': 'COOL',
    '🆓': 'FREE', '🆔': 'ID', '🆕': 'NEW', '🆖': 'NG', '🆗': 'OK',
    '🆘': 'SOS', '🆙': 'UP', '🆚': 'VS',

    # Full A-Z boxed (manually added)
    '🅿️': 'P', '🆀': 'Q', '🆁': 'R', '🆂': 'S', '🆃': 'T',
    '🆄': 'U', '🆅': 'V', '🆆': 'W', '🆇': 'X', '🆈': 'Y', '🆉': 'Z',
    '🅰': 'A', '🅱': 'B', '🅾': 'O', '🅿': 'P',

    # Emoji 0-9 (opsional untuk konsistensi)
    '0️⃣': '0', '1️⃣': '1', '2️⃣': '2', '3️⃣': '3', '4️⃣': '4',
    '5️⃣': '5', '6️⃣': '6', '7️⃣': '7', '8️⃣': '8', '9️⃣': '9',

    '🅰': 'A', '🅱': 'B', '🅲': 'C', '🅳': 'D', '🅴': 'E', '🅵': 'F',
    '🅶': 'G', '🅷': 'H', '🅸': 'I', '🅹': 'J', '🅺': 'K', '🅻': 'L',
    '🅼': 'M', '🅽': 'N', '🅾': 'O', '🅿': 'P', '🆀': 'Q', '🆁': 'R',
    '🆂': 'S', '🆃': 'T', '🆄': 'U', '🆅': 'V', '🆆': 'W', '🆇': 'X',
    '🆈': 'Y', '🆉': 'Z',
    # Dengan VS16 (versi dengan emoji modifier) juga
    '🅰️': 'A', '🅱️': 'B', '🅾️': 'O', '🅿️': 'P', '🆄️': 'U', '🅻️': 'L', '🆆️': 'W',
    '🅸️': 'I', '🅽️': 'N', '🆃️': 'T', '🆂️': 'S', '🆅️': 'V', '🆇️': 'X', '🆈️': 'Y', '🆉️': 'Z',

    '🅐': 'A', '🅑': 'B', '🅒': 'C', '🅓': 'D', '🅔': 'E', '🅕': 'F',
    '🅖': 'G', '🅗': 'H', '🅘': 'I', '🅙': 'J', '🅚': 'K', '🅛': 'L',
    '🅜': 'M', '🅝': 'N', '🅞': 'O', '🅟': 'P', '🅠': 'Q', '🅡': 'R',
    '🅢': 'S', '🅣': 'T', '🅤': 'U', '🅥': 'V', '🅦': 'W', '🅧': 'X',
    '🅨': 'Y', '🅩': 'Z',

    # Enclosed numbers (circled)
    '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
    '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
    '⑪': '11', '⑫': '12', '⑬': '13', '⑭': '14', '⑮': '15',
    '⑯': '16', '⑰': '17', '⑱': '18', '⑲': '19', '⑳': '20',
    '⓪': '0',

    # Fullwidth digits
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
    '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',

    # Fullwidth A-Z
    'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F',
    'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L',
    'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R',
    'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X',
    'Ｙ': 'Y', 'Ｚ': 'Z',

    # Fullwidth a-z
    'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f',
    'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l',
    'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r',
    'ｓ': 's', 'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x',
    'ｙ': 'y', 'ｚ': 'z',

    # Fancy bold letters a-z (𝐚 – 𝐳)
    '𝐚': 'a', '𝐛': 'b', '𝐜': 'c', '𝐝': 'd', '𝐞': 'e', '𝐟': 'f',
    '𝐠': 'g', '𝐡': 'h', '𝐢': 'i', '𝐣': 'j', '𝐤': 'k', '𝐥': 'l',
    '𝐦': 'm', '𝐧': 'n', '𝐨': 'o', '𝐩': 'p', '𝐪': 'q', '𝐫': 'r',
    '𝐬': 's', '𝐭': 't', '𝐮': 'u', '𝐯': 'v', '𝐰': 'w', '𝐱': 'x',
    '𝐲': 'y', '𝐳': 'z',

    # Math double-struck (𝔸 – 𝕫)
    '𝔸': 'A', '𝔹': 'B', 'ℂ': 'C', '𝔻': 'D', '𝔼': 'E', '𝔽': 'F',
    '𝔾': 'G', 'ℍ': 'H', '𝕀': 'I', '𝕁': 'J', '𝕂': 'K', '𝕃': 'L',
    '𝕄': 'M', 'ℕ': 'N', '𝕆': 'O', 'ℙ': 'P', 'ℚ': 'Q', 'ℝ': 'R',
    '𝕊': 'S', '𝕋': 'T', '𝕌': 'U', '𝕍': 'V', '𝕎': 'W', '𝕏': 'X',
    '𝕐': 'Y', 'ℤ': 'Z',

    '𝕒': 'a', '𝕓': 'b', '𝕔': 'c', '𝕕': 'd', '𝕖': 'e', '𝕗': 'f',
    '𝕘': 'g', '𝕙': 'h', '𝕚': 'i', '𝕛': 'j', '𝕜': 'k', '𝕝': 'l',
    '𝕞': 'm', '𝕟': 'n', '𝕠': 'o', '𝕡': 'p', '𝕢': 'q', '𝕣': 'r',
    '𝕤': 's', '𝕥': 't', '𝕦': 'u', '𝕧': 'v', '𝕨': 'w', '𝕩': 'x',
    '𝕪': 'y', '𝕫': 'z',

    # Mathematical italic and script variants
    '𝒜': 'A', '𝒞': 'C', '𝒟': 'D', '𝒢': 'G', '𝒥': 'J', '𝒦': 'K',
    '𝒩': 'N', '𝒪': 'O', '𝒫': 'P', '𝒬': 'Q', '𝒮': 'S', '𝒯': 'T',
    '𝒰': 'U', '𝒱': 'V', '𝒲': 'W', '𝒳': 'X', '𝒴': 'Y', '𝒵': 'Z',
    '𝒶': 'a', '𝒷': 'b', '𝒸': 'c', '𝒹': 'd', '𝑒': 'e', '𝒻': 'f',
    '𝑔': 'g', '𝒽': 'h', '𝒾': 'i', '𝒿': 'j', '𝓀': 'k', '𝓁': 'l',
    '𝓂': 'm', '𝓃': 'n', '𝑜': 'o', '𝓅': 'p', '𝓆': 'q', '𝓇': 'r',
    '𝓈': 's', '𝓉': 't', '𝓊': 'u', '𝓋': 'v', '𝓌': 'w', '𝓍': 'x',
    '𝓎': 'y', '𝓏': 'z',

    # Superscript & Subscript Numbers
    '⁰': '0', '¹': '1', '²': '2', '³': '3',
    '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',

    '₀': '0', '₁': '1', '₂': '2', '₃': '3',
    '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',

    # Greek Lookalikes
    'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H',
    'Ι': 'I', 'Κ': 'K', 'Μ': 'M', 'Ν': 'N', 'Ο': 'O',
    'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X',

    # Roman Numerals
    'Ⅰ': '1', 'Ⅱ': '2', 'Ⅲ': '3', 'Ⅳ': '4', 'Ⅴ': '5',
    'Ⅵ': '6', 'Ⅶ': '7', 'Ⅷ': '8', 'Ⅸ': '9', 'Ⅹ': '10',

    # Braille Patterns
    '⠁': 'A', '⠃': 'B', '⠉': 'C', '⠙': 'D', '⠑': 'E', '⠋': 'F',
    '⠛': 'G', '⠓': 'H', '⠊': 'I', '⠚': 'J', '⠅': 'K', '⠇': 'L',
    '⠍': 'M', '⠝': 'N', '⠕': 'O', '⠏': 'P', '⠟': 'Q', '⠗': 'R',
    '⠎': 'S', '⠞': 'T', '⠥': 'U', '⠧': 'V', '⠺': 'W', '⠭': 'X',
    '⠽': 'Y', '⠵': 'Z',

    # Regional Indicator Symbols
    '🇦': 'A', '🇧': 'B', '🇨': 'C', '🇩': 'D', '🇪': 'E',
    '🇫': 'F', '🇬': 'G', '🇭': 'H', '🇮': 'I', '🇯': 'J',
    '🇰': 'K', '🇱': 'L', '🇲': 'M', '🇳': 'N', '🇴': 'O',
    '🇵': 'P', '🇶': 'Q', '🇷': 'R', '🇸': 'S', '🇹': 'T',
    '🇺': 'U', '🇻': 'V', '🇼': 'W', '🇽': 'X', '🇾': 'Y',
    '🇿': 'Z',

    # Small Caps Unicode
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ғ': 'f',
    'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l',
    'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r',
    's': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x',
    'ʏ': 'y', 'ᴢ': 'z', 'Ø': 'O',

    # Greek
    'Α': 'A',  # Alpha
    'Β': 'B',  # Beta
    'Ε': 'E',  # Epsilon
    'Ζ': 'Z',  # Zeta
    'Η': 'H',  # Eta
    'Ι': 'I',  # Iota
    'Κ': 'K',  # Kappa
    'Μ': 'M',  # Mu
    'Ν': 'N',  # Nu
    'Ο': 'O',  # Omicron
    'Ρ': 'P',  # Rho
    'Τ': 'T',  # Tau
    'Υ': 'Y',  # Upsilon
    'Χ': 'X',  # Chi
    'Λ': 'A',  # Lambda (🔴 kasus kamu)
    'Δ': 'A',  # Delta (opsional)

    # Cyrillic (Russian lookalikes)
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x',
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'Х': 'X',

    # 
    'ℬ': 'B', 'ℰ': 'E', 'ℱ': 'F', 'ℋ': 'H', 'ℐ': 'I', 'ℒ': 'L',
    'ℳ': 'M', 'ℛ': 'R', 'ᗯ': 'W',  # Looks like capital W
    'ᗷ': 'B',  # Looks like capital B
    'ᗩ': 'A',
    'ᒪ': 'L',
    'ᑎ': 'N',
    'ᑌ': 'U',
    'ᗰ': 'M',
    'ᑭ': 'P',
    'ᑫ': 'Q',

    # 
    'в': 'b', 'є': 'e', 'т': 't',
    # Greek
    'ρ': 'p', 'σ': 'o', 'η': 'n',

    # Cyrillic & Greek lookalike Latin
    'Α': 'A', 'А': 'A', 'Β': 'B', 'В': 'B', 'С': 'C', 'Е': 'E', 'Ε': 'E',
    'Η': 'H', 'Н': 'H', 'Ι': 'I', 'І': 'I', 'Ј': 'J', 'Κ': 'K', 'К': 'K',
    'Μ': 'M', 'М': 'M', 'Ν': 'N', 'О': 'O', 'Ο': 'O', 'Ρ': 'P', 'Р': 'P',
    'Ѕ': 'S', 'Τ': 'T', 'Т': 'T', 'Χ': 'X', 'Х': 'X', 'Υ': 'Y', 'Ү': 'Y',
    'а': 'a', 'с': 'c', 'е': 'e', 'є': 'e', 'ҽ': 'e', 'ɡ': 'g', 'һ': 'h',
    'і': 'i', 'ӏ': 'i', '¡': 'i', 'ј': 'j', 'ο': 'o', 'о': 'o', 'ө': 'o',
    'п': 'n', 'η': 'n', 'ρ': 'p', 'р': 'p', 'ѕ': 's', 'т': 't', 'ѵ': 'v',
    'ν': 'v', 'в': 'b', 'х': 'x', 'χ': 'x', 'у': 'y', 'ү': 'y',

    # Visual digit clones
    '〇': '0', 'З': '3', 'Ƽ': '5', '߈': '4'
}

def strip_urls_and_timestamps(text: str) -> str:
    # Hapus URL penuh (http, https, www)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Hapus URL shortener umum seperti bit.ly, t.co, dll.
    text = re.sub(r'\b(bit\.ly|tinyurl\.com|t\.co|goo\.gl|linktr\.ee)/\S+', '', text)

    # Hapus timestamp video dalam format 00:12 atau 1:02:03
    text = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', text)

    return text

def strip_html_tags(text: str) -> str:
    # Hapus seluruh tag HTML dan ambil teksnya saja
    return BeautifulSoup(text, "html.parser").get_text()

def strip_symbols_prefix(text: str) -> str:
    # Ubah @mention dan #hashtag menjadi kata biasa tanpa simbolnya
    return re.sub(r'[@#](\w+)', r'\1', text)

# Fungsi utama normalisasi teks
def normalize_text(text: str) -> str:
    # Hapus tag HTML
    text = strip_html_tags(text)

    # Hapus URL, shortener, dan timestamp
    text = strip_urls_and_timestamps(text)

    # Hapus simbol @ dan # di awal kata (biarkan katanya tetap ada)
    text = strip_symbols_prefix(text)

    # Ganti karakter spesial berdasarkan peta karakter
    text = ''.join(CHARACTER_MAP.get(char, char) for char in text)

    # Normalisasi Unicode dan hapus karakter combining (misalnya aksen atau garis bawah panjang)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])

    # Hapus karakter zero-width/invisible seperti ZWJ dan ZWNJ
    text = re.sub(r'[\u200B\u200C\u200D\uFEFF]', '', text)

    # Hapus simbol/emoji non-informasi, hanya pertahankan huruf, angka, spasi, dan dash
    text = re.sub(r'[^\w\s\-]', ' ', text)

    # Ubah ke huruf kecil dan hapus spasi di awal/akhir
    return text.lower().strip()

def tokenize_text(tokenizer, data):
    return tokenizer(data['text'], max_length=512, truncation=True, padding='max_length')
