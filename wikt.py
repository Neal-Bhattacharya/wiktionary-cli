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
              'Japanese',
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

def clean_word(word):
    word = word.strip()
    word = re.sub("ā", "a", word)
    word = re.sub("ē", "e", word)
    word = re.sub("ī", "i", word)
    word = re.sub("ō", "o", word)
    word = re.sub("ū", "u", word)
    return word


def get_user_word():
    word = ""
    while word == "":
        try:
            prompt = "Enter word " + color("(" + quit_word + " to quit)", "green")
            prompt += "\n>"
            word = clean_word(input(prompt))
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

def parse_lemma(word_def):
    arr = word_def.split("of")
    if len(arr) == 1:
        return None
    lemma = arr[-1]
    if lemma.count("\n") > 1:
        lemma = lemma[0:lemma.index("\n")]
    if lemma.count(" ") > 1:
        return None
    return re.sub(r'[^\w\s]', '', lemma).strip()

def parse_json(dict_obj, single_lang):

    langs = {}
    all_langs = []
    lemmas_found = False

    for v in dict_obj.values():
        try:
            for x in range(0, len(v)):
                word = v[x]
                lang = word['language']
                all_langs.append(lang)
                if single_lang is not None and lang != single_lang:
                    continue
                if limit_langs and lang not in user_langs:
                    continue
                part_of_speech = word['partOfSpeech']
                if lang not in langs.keys():
                    langs[lang] = {
                        'lemmas': set(),
                        'new_line_defs': set(),
                        'parts_of_speech': {}
                    }
                if part_of_speech not in langs[lang]['parts_of_speech']:
                    langs[lang]['parts_of_speech'][part_of_speech]= []
                for definition in word['definitions']:
                    def_txt = next(iter(definition.values())).strip()
                    if def_txt in langs[lang]['new_line_defs']: continue
                    if def_txt != "":
                        for y in def_txt.split("\n"): langs[lang]['new_line_defs'].add(y.strip())
                        def_txt = def_txt.replace("\n", "\n          - ")
                        lemma = parse_lemma(def_txt)
                        if lemma:
                            langs[lang]['lemmas'].add(lemma)
                            lemmas_found = True
                        langs[lang]['parts_of_speech'][part_of_speech].append(def_txt)
        except Exception as e:
            print("Error: " + str(e))
            return None
    if (not langs) or (len(langs) == 0):
        print(color("Word not found in specified languages.", "yellow"))
        print("\nDefinitions found in these languages:")
        i = 1
        for lang in all_langs:
            print("{}. {}".format(i,lang))
            i = i + 1
    return langs, lemmas_found



def print_out(langs):
    if (not langs) or (len(langs) == 0):
        return
    print_sep()
    for l in langs.keys():
        print(color(l, "blue"))
        for p in langs[l]['parts_of_speech']:
            print("  " + str(p))
            i = 1
            for d in langs[l]['parts_of_speech'][p]:
                print("       " + str(i) + ". " + str(d.strip()))
                i += 1

def handle_lemmas(langs):
    lemma_dict = {}
    i = 1
    for lang in langs:
        for lemma in langs[lang]['lemmas']:
            lemma_dict[i] = (lemma, lang)
            i += 1
    print_sep()
    one_lemma = i == 2
    print("\nLemma{} detected:".format("" if one_lemma else "s"))
    for index in lemma_dict:
        print("{}. {}".format(index, lemma_dict[index][0]))
    prompt = "Press enter to look up lemma or new word" if one_lemma else "Enter 1-{} or new word".format(i-1)
    prompt += "\n>"
    inp = input(prompt).strip()
    integer_entered = False
    try:
        word = lemma_dict[int(inp)][0]
        integer_entered = True
    except (ValueError, KeyError):
        word = inp
    if word == quit_word: goodbye()
    if one_lemma and word == "":
        word = lemma_dict[1][0]
    json = get_word_json(clean_word(word))
    if json is None:
        print(color("Word not found.", "yellow"))
        print_sep()
        return
    parsed = parse_json(json, lemma_dict[int(inp)][1] if integer_entered else None)
    print_out(parsed[0])
    print_sep()

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
        parsed = parse_json(json, None)
        print_out(parsed[0])
        # Lemmas detected
        if parsed[1]:
            handle_lemmas(parsed[0])
            continue
        print_sep()

if __name__ == "__main__":
    main()
