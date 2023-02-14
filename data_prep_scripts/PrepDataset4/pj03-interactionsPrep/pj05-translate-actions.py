import os
import json
from collections import Counter
from datetime import datetime


# Run this file from the root of this project file.
currDir = os.getcwd() + "/code/ProvSegments/Dataset_4/User Interactions/extractingActionDetails/"
fileToConvert = currDir+"p8.json"
outDir = os.getcwd() + "/scripts/newData/Dataset_4/"
outFileName = 'Panda_P8_InteractionsLogs.json'

outData = {
    "data": []
}
originalTypes = []
oTimeFormat = '%H:%M:%S:%f'


def typeTranslate(event, eventTypeKey = "action"):
    #switch case for each type of event.
    etype = event[eventTypeKey]
    #convert time to miliseconds
    ajdTime = datetime.strptime(event['time'],oTimeFormat)
    event["time"] = ajdTime.hour*3600000+ajdTime.minute * \
        60000+ajdTime.second*1000+ajdTime.microsecond/1000
    # print(event)
    if(etype == "query"):
        event['InteractionType'] = "Search"
        event['Text'] = event["query_str"]
        return event
    elif (etype == "expand"): 
        event['InteractionType'] = "Doc_open"
        event["ID"] = event["uuid"]
        return event
    elif (etype == "selectedDateOnHistogram"):
        event['InteractionType'] = "selectedDateOnHistogram"
        return event
    elif (etype == "collapse"):
        event['InteractionType'] = "closeDoc"
        event["ID"] = event["uuid"]
        return event
    elif (etype == "viewDocument"):
        event['InteractionType'] = "Doc_open"
        event["ID"] = event["id"]
        return event
    elif (etype == "playAudioFileInNewWindow"):
        event['InteractionType'] = "Reading"
        event["ID"] = event["documentURL"]
        return event
    elif (etype == "keepAlive"):
        event['InteractionType'] = "keepAlive"
        return event
    elif (etype == "paging"):
        event['InteractionType'] = "paging"
        return event
    elif (etype == "noteUpdated"):
        event['InteractionType'] = "Add Note"
        event['Text'] = event["note"]
        event["ID"] = event["recordID"]
        return event
    elif (etype == "createDocumentBucket"):
        event['InteractionType'] = "Add Note"
        event['Text'] = event["tag"]
        return event
    elif (etype == "addToDocumentBucket"):
        event['InteractionType'] = "Shoebox" #I think it need this to be reading cause I don't have the text to include with the event.
        event["ID"] = event["documentUUID"]
        return event
    elif (etype == "dispositionUpdated"):
        event['InteractionType'] = "Highlight"
        event["ID"] = event["recordID"]
        event["Text"] = event["note"]
        return event
    elif (etype == "domainHome"):
        event['InteractionType'] = "domainHome"
        return event
    elif (etype == "search"):
        event['InteractionType'] = "search"
        return event
    elif (etype == "initialized"):
        event['InteractionType'] = "initialized"
        return event
    else:
        return event

with open(fileToConvert) as file:
    data = json.load(file)
    for e in data:
        originalTypes.append(e["action"])
    #count the types of events
    oTypeFreq = Counter(originalTypes)
    print(oTypeFreq)
    
    for e in data:
        outData["data"].append(typeTranslate(e))

    print("total events: "+str(len(data)))
    print("events captured in new output file: "+str(len(outData["data"])))

with open(outDir+outFileName, 'w') as output_file:
    json.dump(outData, output_file)

print("-----done-----> Histogram file generated to: "+currDir+outFileName)
