import requests
import re
import ast
import sys

# TODO: Implement non-lemmatized form detection

# Set this to True to only list langs in `user_langs`
limit_langs = True

# Disable console colors
disable_colors = False

# If this is true, do not perform SSL verification
# Dangerous! see https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
insecure = False

quit_word = "q"

# These must be entered exactly as they appear in Wiktionary headings
user_langs = {
              'English',
              'French',
              'Spanish',
              'Ancient Greek',
              'Latin',
              'German'
              }

def color(s, col):
    if disable_colors: return s
    green = "\033[32m"
    yellow = "\033[93m"
    blue = "\033[94m"
    escape = "\033[0m"
    match col.lower():
        case "green":  return green + s + escape
        case "blue":   return blue + s + escape
        case "yellow": return yellow + s + escape
        case _:        return s

def print_sep():
    print("----------------------------------------")

def goodbye():
    print("\nGoodbye")
    sys.exit()

def get_user_word():
    word = ""
    while word == "":
        try:
            prompt = "Enter word " + color("(" + quit_word + " to quit):\n", "green")
            word = input(prompt).strip()
        except KeyboardInterrupt:
            goodbye()
    return word

def get_word_json(word):
    url = "https://en.wiktionary.org/api/rest_v1/page/definition/" + word
    headers = {"User-Agent" : "https://github.com/Neal-Bhattacharya/wiktionary-cli"}
    res = requests.get(url, verify=not insecure, headers=headers)

    if res.status_code == 404:
        print(color("Word not found.", "yellow"))
        print_sep()
        return None
    raw_str = re.sub('<[^<]+?>', '', res.text)

    parsed_dict = ast.literal_eval(raw_str)
    return parsed_dict


def parse_json(dict_obj):

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
    if (not langs) or (len(langs) == 0):
        print(color("Word not found in specified languages.", "yellow"))
    return langs


def print_out(langs):
    if (not langs) or (len(langs) == 0):
        return
    print_sep()
    for l in langs:
        print(color(l, "blue"))
        for p in langs[l]:
            print("  " + str(p))
            y = 1
            for d in langs[l][p]:
                print("       " + str(y) + ". " + str(d.strip()))
                y += 1
def main():
    if insecure:
        import urllib3
        urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

    while True:
        word = get_user_word()
        if word == quit_word:
            goodbye()
        json = get_word_json(word)
        if json is None:
            continue
        print_out(parse_json(json))
        print_sep()

if __name__ == "__main__":
    main()
