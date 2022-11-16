from collections import Counter
import math
import json
import csv
import sys

##How to access a doc from docs var
##docs[set#][#]
docs = []

##How to access a log or segment item from logs/segments var
##item[set#][participant#][#]
logs = []
segments = []
segKeys = []

path1 = "code/ProvSegments/Dataset_"
path2 = "/User Interactions/"
path21 = "/Segmentation/"
path3 = "_P" #user num
path4 = "_InteractionsLogs.json"
path41 = "_20_4_6_Prov_Segments.csv"
path22 = "/SegKeys/p"
path32 = ".csv"

outputFileName = 'code/ApplicationManifest.json'

mergesegments = int(sys.argv[1])

#Set names
setNames = ["Arms", "Terrorist", "Disappearance", "Panda"]

#Open log/segment JSON
for i in range (1,5): ##4 datasets
    setlogs = []
    setsegments = []
    setKeywords = []
    for j in range (1,9): ##8 participants

        ##Getting log json for dataset/participant
        with open(path1+str(i)+path2+setNames[i-1]+path3+str(j)+path4) as file:
            file_json = json.load(file)
            setlogs.append(file_json)

        ##Getting segments and converting CSV to json for dataset/participant
        with open(path1+str(i)+path21+setNames[i-1]+path3+str(j)+path41) as file:
            reader = csv.DictReader(file)
            csvjson = [json.dumps(d) for d in reader]
            setsegments.append(csvjson);

        #Getting keywords associated with segments
        with open(path1+str(i)+path22+str(j)+path32) as file:
            reader2 = csv.reader(file)
            setKeywords.append(list(reader2));

    logs.append(setlogs)
    segments.append(setsegments)
    segKeys.append(setKeywords)

#Create segment JSON, cluster short segments into previous segments
segment_json = []
min_segment_length = 0;

#Create a list for the superlatives/overview content to be hostes
superlatives = []

#for each dataset and participant
for _set in range(0,4):
    superlatives.append([])
    #for each particiapant
    for _id in range(0,8):

        ##default state for new set of segments
        current_segment = 0
        # new_segment = True;
        segment_start = 0;
        segment_end = 0;
        current_segment_json = []

        #set up superlatives for this individual to be updated later
        superlatives[_set].append({
            "totalInteractions": len(logs[_set][_id]), # count the number of recorded interactions.
            "segCount": len(segments[_set][_id]), #total number of segments (should be 11 for everyone)
            # average expected number of interactions in a segment
            "meanInteractions": len(logs[_set][_id])/len(segments[_set][_id]),
            "sumSquaresInteractions":-1.0,
            "stdIntRate":-1.0, #The standard deviation in the number of interactions happening in a segment
            "topicCount": -1, #total number of uniquely encountered topics
            "allTopics": [], #List of all the topics encountered over time (seomg SegKeys file)
            "topics": [],   #list of the top three topics encountered by user
            "searchCount":-1, #counting the raw number of searches made (including duplicates)
            "mostSearchesinSeg":-1, #counts maximum number of searches made in a segment. Updates when a segment is processed where there are more searches than this value/
            "mostSearchSeg": -1, #identifyer for the segment with the most raw searches made.
            "searches": [], #list of all the search terms.
            "breakpointSearches": [], #set of three searches that are selected from the list of all searches. One from the beginning, one from the middle and one from the end. At the time of writing, these are just systematically chosen, but are not significant searches.
            "openCount":-1, #counts the number of documents opened (including duplicates)
            "opens" : [],  #list of document ids to identify the number of unique documents seen. (specifically helpful for dataCoverage.)
            "mostOpensinSeg": -1, #counts the maximum number of opens in a segment. Updates when a segment has more opens than a previous segment
            "newestSeg": -1, # the segment where the most docuemts were open. Updates when mostOpensinSeg updates.
            "dataCoverage": -1.0,
            "longestSegTime":-1,
            "longSeg": -1,
            'longOpenRate': "some documents",
            "mostActive" : -3, #based on z-scores for interactions. so starting way below the average
            "mostActiveSegment": -1  # the associated segment for the most active behavior
        })

        #for all the corresponding segments
        for i,segment in enumerate(segments[_set][_id]):

            ##string-indexable segment
            stringjson = json.loads(segment)

            ##get min size, ignore if arg was 0;
            min_segment_length = float(json.loads(segments[_set][_id][-1])['end'])/24
            if mergesegments == 0:
                min_segment_length = 0

            ##get start and end times
            segment_start = int(float(stringjson['start']))
            segment_end = int(float(stringjson['end']))

            #first segment will always exist, ignore later segments that are short
            if(current_segment!=0 and segment_end-segment_start < min_segment_length):
                current_segment_json[current_segment-1].update({'end' : segment_end})

            #set up individual segment's json details with some variables to be calculated later.
            current_segment_json.append({
                "dataset" : _set+1,
                "pid" : _id+1,
                "sid" : current_segment,
                "start" :  int(segment_start),
                "end" : int(segment_end),
                "length" : int(segment_end-segment_start),
                "interactionCount" : 0,
                "squareMeanDiffInteraction":0,
                "z_interactions": 0.0,  # z-score for the interaction rate.
                "keywords" : segKeys[_set][_id][i]
            })
            
            # capture the keywords in the superlatives object
            # print(current_segment_json[-1]["keywords"])
            if current_segment_json[-1]["keywords"] is not None:
                # print(superlatives[_set][_id])
                superlatives[_set][_id].update({
                    "allTopics" : superlatives[_set][_id]["allTopics"] + (current_segment_json[-1]["keywords"])
                })
            current_segment = current_segment+1
        
        ##calculate length for resulting sections
        for segment in current_segment_json:
            segment.update({"length" : int(segment['end']-segment['start'])})
            
            #find the longest segment for the superlatives
            if segment['length'] > superlatives[_set][_id]["longestSegTime"]:
                # print(str(segment["length"]) + " ||| " + str(segment["sid"]) + " ||| "+ str(segment))
                superlatives[_set][_id].update({"longSeg" : segment["sid"]+1,
                "longestSegTime" : segment["length"]})

            #TODO Pull out keywords and add count to superlatives obj 
            
            segment_json.append(segment)

        #count the frequency of different topics and sort in decending order.
        superlatives[_set][_id].update(
            {"topicCounter": Counter(superlatives[_set][_id]["allTopics"]).most_common()}
            )
        #count number of unique topics
        superlatives[_set][_id].update({
            "topicCount": len(superlatives[_set][_id]["topicCounter"])
        })
        #set the top three topics for display in system.
        superlatives[_set][_id].update({"topics": [superlatives[_set][_id]["topicCounter"][0][0],
                                        superlatives[_set][_id]["topicCounter"][1][0],
                                        superlatives[_set][_id]["topicCounter"][2][0] ] })


#After the previous set of loops, we have JSON for segments.

#Now we go through and add pid, segment ids, dataset ids, and counts for how many interactions are in the segment
_segment = 1
for _set in range(0,4):
    for _id in range(0,8):
        # print(_set, _id)
        def makeBlankArray(length):
            a = []
            for i in range(length):
                a.append(0)
            return a

        eventsBySeg = {
            "Search": makeBlankArray(superlatives[_set][_id]["segCount"]),
            "Doc_open": makeBlankArray(superlatives[_set][_id]["segCount"])
        }
        for event in logs[_set][_id]:

            event.update({'dataset' : _set+1})
            event.update({'PID': _id+1})

            for segment in segment_json: # room to improve this loop cause there's lots of extra cycles that hit the if statement and do nothing. not sure if it's worth fixing though.
                if(event['time']/10 >= segment['start'] and event['time']/10 <= segment['end'] and segment['pid']==_id+1 and segment['dataset']==_set+1):
                    event.update({'segment' : segment['sid']})
                    segment.update({"interactionCount" : segment["interactionCount"]+1})
                    #set the squared mean difference for determing z statistics for interactions.
                    segment.update(
                        {"squareMeanDiffInteraction": (superlatives[_set][_id]["meanInteractions"] - segment["interactionCount"])**2})
                    superlatives[_set][_id]["sumSquaresInteractions"] += segment["squareMeanDiffInteraction"]
                    if event["InteractionType"] == "Search":
                        superlatives[_set][_id]["searches"].append(event["Text"])
                        eventsBySeg["Search"][event["segment"]] += 1
                    if event["InteractionType"] == "Doc_open":
                        superlatives[_set][_id]["opens"].append(
                            event["ID"])
                        eventsBySeg["Doc_open"][event["segment"]] += 1
        #review each saved number of seraches and doc opens to identify the segments with the most events.
        for i in range(superlatives[_set][_id]["segCount"]):
            if eventsBySeg["Search"][i] > superlatives[_set][_id]["mostSearchesinSeg"] :
                superlatives[_set][_id].update({
                    "mostSearchesinSeg": eventsBySeg["Search"][i],
                    "mostSearchSeg": i+1
                })
            if eventsBySeg["Doc_open"][i] > superlatives[_set][_id]["mostOpensinSeg"]:
                superlatives[_set][_id].update({
                    "mostOpensinSeg": eventsBySeg["Doc_open"][i],
                    "newestSeg": i+1
                })
        #finally, count the number of searches and opens completed (with duplicates)
        superlatives[_set][_id]["searchCount"] = len(
            superlatives[_set][_id]["searches"])
        superlatives[_set][_id]["openCount"] = len(
            superlatives[_set][_id]["opens"])

        

        searchBreakpointModulo = math.floor(superlatives[_set][_id]["searchCount"]/4) # deviding by 4 since I wan to split the set into 3 pieces and don't want to call attention to the first or last search.
        superlatives[_set][_id]["breakpointSearches"] = [\
            superlatives[_set][_id]["searches"][searchBreakpointModulo*1],
            superlatives[_set][_id]["searches"][searchBreakpointModulo*2],
            superlatives[_set][_id]["searches"][searchBreakpointModulo*3]]

        #Calculate Coveage for each user
        #List of document counts for each dataset
        dataDocCount = [102,159,152,12714]
        #remove document opens for repeated documents (i.e., only count uniuque documents)
        superlatives[_set][_id]["opens"] = Counter(superlatives[_set][_id]["opens"])
        #divide the unique documents by the number of documents available to arrive at data coverage.
        superlatives[_set][_id]["dataCoverage"] = len(superlatives[_set][_id]["opens"])/dataDocCount[_set]


# take a square root to get standard deviation in interactions
for _set in range(0, 4):
    for _id in range(0, 8): 
        superlatives[_set][_id].update({"stdIntRate": (
            superlatives[_set][_id]["sumSquaresInteractions"] / superlatives[_set][_id]["segCount"])**0.5 })

#setting z-scores for interactions and updating with the most active segment.
for segment in segment_json:
    currentSet = segment["dataset"]-1
    currentId = segment["pid"]-1
    segment.update({"z_interactions": (segment["interactionCount"] - superlatives[currentSet]
                   [currentId]["meanInteractions"])/superlatives[currentSet][currentId]["stdIntRate"]})
    if superlatives[currentSet][currentId]["mostActive"] < (segment["z_interactions"]):
        superlatives[currentSet][currentId].update({"mostActive" : segment["z_interactions"]})
        superlatives[currentSet][currentId].update({"mostActiveSegment":  segment["sid"]-1})


def calcLongestSegReadRate(interactionRatio):
    documentInteractionsPerSegment = abs(interactionRatio)
    if (interactionRatio > 0):
        isPositive = True
    else:
        isPositive = False
    quality = ""
    if (documentInteractionsPerSegment > 0.09):
        if (isPositive):
            quality = "much more active than usual"
        else:
            quality = "much less active than usual"
    elif (documentInteractionsPerSegment > 0.03):
        if (isPositive):
            quality = "more active than usual"
        else:
            quality = "less active than usual"
    else:
        quality = "as active as usual"

    return quality
# final loop for calculating superlatives
for _set in range(0, 4):
    for _id in range(0, 8):
        currSegNum = 0

        # set the activity rate in longest period
        longSegIdx = superlatives[_set][_id]["longSeg"]-1
        longInteractionRatio = segment_json[_set*11+_id+longSegIdx]["z_interactions"]
        # print(longInteractionRatio)
        superlatives[_set][_id].update(
            {"longOpenRate": calcLongestSegReadRate(longInteractionRatio)})
        
final_json = {}



final_json.update({"segments": segment_json})


final_json.update({'interactionLogs' : logs})

final_json.update({"superlatives" : superlatives})


with open(outputFileName, 'w') as json_file:
    json.dump(final_json, json_file, indent=4)
    print("----> success: file written to "+outputFileName)
# print(json.dumps(final_json, indent=4))
