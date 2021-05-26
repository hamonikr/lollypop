from locale import strcoll

_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'W', 'X', 'Y', 'Z', 'Z']
_CHARS = ['阿', '八', '嚓', '哒', '妸', '发', '旮', '哈', '讥', '咔', '垃', '痳',
          '拏', '噢', '妑', '七', '呥', '扨', '它', '穵', '夕', '丫', '帀', '做']
_RANGES = [(l, c, cc) for ((l, c), (ll, cc)) in
           zip(list(zip(_LETTERS, _CHARS))[:-1], list(zip(_LETTERS, _CHARS))[1:])]
_EXCEPTIONS = {'曾': 'Z', '沈': 'S', '酢': 'Z'}

def index_of(string):
    """
        Return the (Pinyin-ized) index character in upper case.
        Return '#' if it's a digit.
        Return '…' if it's not recognizable in this locale.
        Locale: zh_CN.
        @param string as str
        @return str
    """
    head = string[0]

    if head.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        return head.upper()

    if head in '1234567890':
        return '#'

    if head in _EXCEPTIONS:
        return _EXCEPTIONS[head]

    for letter, char, next_char in _RANGES:
        if strcoll(char, head) <= 0 and strcoll(head, next_char) <= 0:
            return letter

    return '?'
