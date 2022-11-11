import os
import json
import re
from collections import Counter
import nltk
from nltk.tokenize import RegexpTokenizer

# Run this file from the root of this project file.
currDir = os.getcwd() +"/code/ProvSegments/Dataset_4/Documents/"
fileToConvert = currDir+"dataset4.json"
outFileName = 'document-histograms-dataset4.json'

mainTextKey = "contents"

outData = {
    "documents": [],
    "words": []
}

def filterWords(text):
    # split by words
    tk = RegexpTokenizer(r'\w+')
    words = nltk.tokenize.word_tokenize(text)
     # todo: Remove the odd timing characters
    
     # filter out punctuation.
    nonPunct = re.compile('.*[A-Za-z0-9].*')
    words = [w for w in words if nonPunct.match(w)]

    #filter out timing characters
    nonTime = re.compile('(\d\d?[:]\d\d[:]\d\d)')
    words = [w for w in words if not nonTime.match(w)]
    
    # filter out unnecesary speaker toekens
    nonSpk = re.compile('(spk_\d)')
    words = [w for w in words if not nonSpk.match(w)]

    # set to lower case
    for i in range(len(words)):
        words[i] = words[i].lower()
    
    # count frequencies of strings
    freq = Counter(words)
    return [words,freq]


def expandVocab(words, vocabulary=[]):
    for word in words:
        if word not in vocabulary:
            vocabulary.append(word)
    return vocabulary


def generateVocab(data):
    vocabulary = []
    for d in data:
        [w, f] = filterWords(d[mainTextKey])
        vocabulary = expandVocab(w)
        # vocabulary = [w for w in words if w in vocabulary ]
        print("next document processed, vocabulary expanded to: "+ str(len(vocabulary)))
    return vocabulary



def calcFrequencies(doc, vocabulary):
    print("generating word histogram for "+doc["tapeName"])
    hist = []
    [w, f] = filterWords(doc[mainTextKey])
    seenwords = 0
    totalWords = len(w)
    for v in range(len(vocabulary)):
        if vocabulary[v] in w:
            hist.append(f[vocabulary[v]]/totalWords)
            seenwords = seenwords + 1
        else:
            hist.append(0.0)
    return hist




with open(fileToConvert) as file:
    data = json.load(file)
    #extract the relevant parts of each document.
    v = generateVocab(data)
    for d in range(len(data)):
        freq = calcFrequencies(data[d], v)
        reformatedDocument = {
            "id": data[d]["audioURL"],
            "histogram":freq
        }
        outData["documents"].append(reformatedDocument)
    # Also Add in the words list here too.
    outData["words"]= v
    print(len(outData["words"][0]))
        
with open(currDir+outFileName, 'w') as output_file:
    json.dump(outData, output_file)

print("-----done-----> Histogram file generated to: "+currDir+outFileName)
