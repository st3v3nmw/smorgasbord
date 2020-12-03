from wiktionaryparser import WiktionaryParser
import json
import urllib.request

# Using Anki Connect addon
def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def invoke(action, **params):
    requestJson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestJson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

parser = WiktionaryParser()
ws = input("Enter comma separated words: ").split(',')
# parser.set_default_language('German')

for w in ws:
    word = parser.fetch(w)
    audio_file = 'a'
    audio = []

    try:
        audio.append({
                        "url": "https:" + word[0]['pronunciations']['audio'][0],
                        "filename": w + "-en.mp3", # en English suffix
                        "fields": [
                            "Audio"
                        ]
                    })
    except IndexError:
        pass

    try:
        definition = word[0]['definitions'][0]
    except IndexError:
        print(f"{w} not found")
        print(word)
        continue

    ipa = ""
    priority = 0 # higher is better
    # print(word[0]['pronunciations']['text'])
    for pr in word[0]['pronunciations']['text']:
        if pr[:3] == 'IPA': # priority 4
            if priority < 4:
                ipa = pr[5:]
        elif pr[:22] == '(General American) IPA': # priority 3
            if priority < 3:
                ipa = pr[25:]
        elif pr[:8] == '(US) IPA': # priority 3
            if priority < 3:
                ipa = pr[10:]
        elif pr[:8] == '(UK) IPA': # priority 2
            if priority < 2:
                ipa = pr[10:]
        elif pr[:28] == '(Received Pronunciation) IPA': # priority 1
            if priority < 1:
                ipa = pr[30:]
        elif pr[:23] == '(British, America) IPA': # priority 3
            if priority < 4:
                ipa = pr[25:]
        elif pr[:12] == '(UK, US) IPA': # priority 3
            if priority < 3:
                ipa = pr[14:]
        elif pr[:9] == '(US): IPA': # priority 3
            if priority < 3:
                ipa = pr[11:]
    try:
        examples = definition['examples'][0]
    except IndexError:
        examples = ''

    note = {
            "note":
                {
                    "deckName": "Miscellaneous::English",
                    "modelName": "Vocabulary",
                    "fields": {
                        "Word": w,
                        "Part of Speech": definition['partOfSpeech'],
                        "IPA": ipa,
                        "Definition": definition['text'][1],
                        "Examples": examples
                        },
                    "options": {
                        "allowDuplicate": False,
                        "duplicateScope": "collection"
                        },
                    "audio": []
                }
            }
    
    if len(audio) != 0:
        note["note"]["audio"] = audio

    try:
        result = invoke('addNote', **note)
        print(f"{w} added")
    except Exception as e:
        print(f"{w} {e}")