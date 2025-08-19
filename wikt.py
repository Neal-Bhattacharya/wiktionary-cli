import requests
import re
import ast
import sys

# TODO: Implement non-lemmatized form detection

# Set this to True to only list langs in `user_langs`
limit_langs = False

# Disable console colors
disable_colors = False

# If this is true, do not perform SSL verification
# Dangerous! see https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
insecure = False

# These must be entered exactly as they appear in Wiktionary headings
user_langs = ['English', 'French', 'Spanish', 'Ancient Greek', 'Latin', 'German']

def color(s, color):
    if disable_colors: return s
    GREEN = "\033[32m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ESCAPE = "\033[0m"
    match color.lower():
        case "green":
            return GREEN + s + ESCAPE
        case "blue":
            return BLUE + s + ESCAPE
        case "yellow":
            return YELLOW + s + ESCAPE

def printSep():
    print("----------------------------------------")

def goodbye():
    print("\nGoodbye")
    sys.exit()

def getUserWord():
    word = ""
    while word == "":
        try:
            word = input("Enter word" + color(" (q to quit)", "green")+ "\n>").strip()
        except KeyboardInterrupt:
            goodbye()
    return word

def getWordJson(word):
    url = "https://en.wiktionary.org/api/rest_v1/page/definition/" + word
    res = requests.get(url, verify=not insecure)

    raw_str = re.sub('<[^<]+?>', '', res.text)
    if "404" in raw_str:
        print(color("Word not found.", "yellow"))
        printSep()
        return None
    parsed_dict = ast.literal_eval(raw_str)
    return parsed_dict


def parseJson(dict_obj):

    langs = {}

    for v in dict_obj.values():
        try:
            for x in range(0, len(v)):
                word = v[x]
                lang = word['language']
                if limit_langs and lang not in user_langs:
                    continue
                part_of_speech = word['partOfSpeech']
                if lang not in langs.keys():
                    langs[lang] = {}
                if part_of_speech not in langs[lang].keys():
                    langs[lang][part_of_speech] = []
                for definition in word['definitions']:
                    def_txt = next(iter(definition.values())).strip()
                    if def_txt != "":
                        langs[lang][part_of_speech].append(def_txt)
        except Exception as e:
            print("Error: " + str(e))
            return None

    return langs


def printOut(langs):
    printSep()
    for k in langs.keys():
        print(color(k, "blue"))
        for p in langs[k].keys():
            print("  " + str(p))
            y = 1
            for d in langs[k][p]:
                print("       " + str(y) + ". " + str(d.strip()))
                y += 1
def main():
    if (insecure):
        import urllib3
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

    while True:
        word = getUserWord()
        if word == "q":
            goodbye()
        json = getWordJson(word)
        if json is None:
            continue
        printOut(parseJson(json))
        printSep()

if __name__ == "__main__":
    main()
