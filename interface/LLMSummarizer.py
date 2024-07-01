import json
import csv
import sys
import os # To move through the file tree to get to the .env file with the API Key
import re
import copy
# import math
import traceback  
from dotenv import load_dotenv # Keeping API secrets 
from openai import OpenAI, BadRequestError # Connect to LLM
from fuzzywuzzy import process


load_dotenv()
# A flag to turn off the GPT stuff while still testing. When ready to spend money, set this to true.
useGPT = True

def checkEventType (event, disqualifiedEvents = ["Think_aloud", "Topic_change", "Mouse_hover"]):
    if event["interactionType"] in disqualifiedEvents:
        return False
    else:
        return True

colors = {
  "Doc_open": "crimson",
  "Documents Opened": "crimson",
  "Topics": "0096FF",
  "Search": "#009420",
  "Searches": "#009420",
  "Add note": "#4278f5",
  "Notes": "#4278f5",
  "Highlight": "#ab8300",
  "Highlights": "#ab8300",
  "Reading": "pink",
  "Keywords": "#0096FF",
  "Dates": "#b16a1f",
  "PersonEnt": "#0096FF",
  "GeoEnt": "#049c9a",
  "barBG": "lightgrey",
  "Average-neg":"blue",
  "Average-pos": "orange",
}

parentDirectory = os.path.join(
    os.path.abspath(os.path.join(os.getcwd(), os.pardir)), os.getcwd()
)

segmentsPath = "6"
participantCnt = "8"
dataset_path = parentDirectory + f"/interface/ApplicationManifest_{segmentsPath}.json"
LLMPartialsDirectory = parentDirectory+f"/data/LLMStages_{segmentsPath}/"


def load_json_file(file_path):
    with open(file_path, "r") as read_file:
        data = json.load(read_file)
    return data

def save_json_to_file(data, filename, overwriteFiles = True, indent = True):
    """
    Save a JSON object to a file.

    Parameters:
    data (dict): The JSON object to save.
    filename (str): The name of the file to save the JSON object in.
    overwriteFiles (bool): Optional - if you are done testing the files and don't want to overwrite files already made, flip this False.
    """
    # Create the directory if it doesn't exist
    if (overwriteFiles):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as file:
            if(indent):
                json.dump(data, file, indent=2)
            else:
                json.dump(data, file, separators=(',', ':'))
    else:
        # Make a file with test as the predicate so not to overwrite the version you like
        filename = filename[:-5]+"-test.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as file:
            if(indent):
                json.dump(data, file, indent=2)
            else:
                json.dump(data, file, separators=(',', ':'))

def merge_json(data1, data2):    
    # Create a dictionary to store the merged data
    merged_data = {}
    
    # Add all entries from the first file to the merged_data
    for entry in data1:
        merged_data[entry['id']] = entry
    
    # Merge entries from the second file
    for entry in data2:
        if entry['id'] in merged_data:
            # If the 'id' already exists, update the existing entry with new data
            merged_data[entry['id']].update(entry)
        else:
            # Otherwise, add the new entry
            merged_data[entry['id']] = entry

    # Convert the merged_data back to a list of objects
    # merged_list = list(merged_data.values())
    # return merged_list
    return merged_data

def remove_properties(obj, properties):
    """
    Removes specified properties from a dictionary if they exist, 
    or if the properties have empty string or empty list values.

    Parameters:
    obj (dict): The dictionary object from which properties are to be removed.
    properties (list): A list of property names (keys) to be removed from the dictionary.

    Returns:
    dict: The dictionary object with the specified properties removed.
    """
    for prop in properties:
        if prop in obj:
            del obj[prop]
    return obj

def return_blank_properties(obj):
    """
    Removes properties from a dictionary if they have empty string or empty list values.

    Parameters:
    obj (dict): The dictionary object from which properties with empty values are to be removed.

    Returns:
    dict: The dictionary object with properties having empty string or empty list values removed.
    """
    props = list(obj.keys())  # Create a list of keys to avoid changing the dictionary size during iteration
    for p in props:
        if obj[p] == '' or obj[p] == []:
            del obj[p]
    return obj

def addContextToInteraction(interaction, allDocuments, allowable_types=["Reading","Doc_open","Highlight","Draging"], propertiesToAppend = ["summary","Geos","People","topics"], propertiesToRemove = ["id", "duration",   "dataset", "PID", "segment"]):
    # Check if the interactionType is in the allowable types
    if interaction.get('interactionType') in allowable_types:
        # Find the corresponding object in the larger object using the 'id' property
        matchingID = interaction.get('id')
        dataToAdd = allDocuments.get(matchingID)
        

        # If a matching object is found, update the obj with its information
        if dataToAdd:
            update_data = {k: dataToAdd[k] for k in propertiesToAppend if k in dataToAdd}
            interaction.update(update_data)

    interaction = remove_properties(interaction, propertiesToRemove)
    interaction = return_blank_properties(interaction)
    
    return interaction


def askGPTMultiple(prompt):
    print("✨ too long ❌ - asking in chunks")

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Determine max token length (adjust if necessary)
    max_token_length = 14000
    response_token_length = 150  # Expected token length of each response

    # Split prompt into segments that fit within max token length
    chunks = []
    while len(prompt) > max_token_length:
        split_index = prompt.rfind(' ', 0, max_token_length)  # find a suitable split point
        if split_index == -1:
            break
        chunks.append(prompt[:split_index+1])
        prompt = prompt[split_index+1:] #get the portion of the string remaining
    chunks.append(prompt) #add remaining string

    sys_msg = [{"role": "system", "content": "Summarize as concisely as possible each chunk of interactions I give you. Update the summary to incorporate each chunk into your summary."}]
    # Initialize with an empty assistant response
    assistant_response = ""

    # Send each segment to the API
    print("preparing message")
    for chunk in range(len(chunks)):
        print(f"message {chunk+1}/{len(chunks)} is {len(chunks[chunk])} characters")

        # Construct the current message set
        current_msg = sys_msg + [{"role":"assistant", "content":assistant_response}, {"role":"user", "content":chunks[chunk]}]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=current_msg, # type: ignore
            max_tokens=response_token_length,  # Adjust based on the desired summary length
            temperature=0.1,  # Adjust for summary precision
        )

        # Update the assistant response for the next segment
        assistant_response = response.choices[0].message.content
        print("assistant says:", assistant_response)
        # msg.append({"role": "assistant", "content": assistant_response}) # type: ignore

    return assistant_response


def askGPTMultiple_broken(prompt):
    print("✨ too long ❌ - asking in chunks")

    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    # Determine max token length (typically 2048 tokens)
    max_token_length = 10000

    # Split prompt into segments that fit within max token length
    chunks = []
    while len(prompt) > max_token_length:
        split_index = prompt.rfind('}', 0, max_token_length)  # find a suitable split point
        if split_index == -1:
            break
        chunks.append(prompt[:split_index+1])
        prompt = prompt[split_index+1:] #get the portion of the string remaining
    chunks.append(prompt) #add remaining string

    msg = [{"role": "system", "content": "Summarize as concisely as possible each chunk of interactions I give you. Update the summary to incorporate each chunk into your summary."}]
    # Send each segment to the API
    print("preparing message")
    for chunk in range(len(chunks)):
        print(f"message {chunk}/{len(chunks)-1} is {len(chunks[chunk])} characters")
        msg.append({"role":"user", "content":chunks[chunk]})

        response = client.chat.completions.create(
            messages=msg, # type: ignore
            model="gpt-3.5-turbo",
            max_tokens=150,  # Adjust based on the desired summary length
            temperature=0.1,  # Adjust for summary precision
        )

        # Update context for the next segment
        current_response = response.choices[0].message.content
        msg.append({"role": "assistant", "content": current_response}) # type: ignore
    return msg[-1]["content"]


def askGPT(prompt):
    print(f"asking ✨GPT: {prompt[:400]}...")
    try:
        # Create a prompt that asks the model to summarize the logs

        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
            max_tokens=150,  # Adjust based on the desired summary length
            temperature=0.1,  # Adjust for summary precision
        )

        return chat_completion.choices[0].message.content
    except BadRequestError as e:
        print(str(e))
        # if 'error' in e and 'code' in e['error'] and e['error']['code'] == 'context_length_exceeded':
        return askGPTMultiple(prompt)
            # return "Error: Maximum context length exceeded. Please reduce the length of your prompt or use a shorter prompt."
        # else:
        #     return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

"""
Finalizes the dataset processing by cleaning up interactions, summarizing segments,
identifying entities, and saving the summaries.

This function performs the following steps:
1. Cleans up each interaction to reduce the token count.
2. Summarizes each segment's interactions using ChatGPT.
3. Identifies entities in each segment summary and overall summary.
4. Parses summaries and adds HTML code to highlight entities.
5. Saves the summaries to files for each user.
"""
def clean_interaction(interaction):
    """
    Cleans an interaction by removing unnecessary parts.

    Parameters:
    interaction (dict): The interaction object to clean.

    Returns:
    dict: The cleaned interaction object.
    """
    keys_to_keep = ['id', 'interactionType', 'time', 'segment', 'summary', 'Geos', 'People', 'topics']
    return {key: interaction[key] for key in keys_to_keep if key in interaction}

def summarize_segment(segment_interactions):
    """
    Summarizes interactions in a segment using ChatGPT.

    Parameters:
    segment_interactions (list): List of interactions in the segment.

    Returns:
    str: The summary of the segment.
    """
    interactions_text = "\n".join([str(interaction) for interaction in segment_interactions])
    prompt = f"Here is a list of interactions from a user's investigation of data. Please provide a concise 500-character explanation focusing on main topics and findings. Include actionable instructions, relevant keywords, and ensure accuracy and completeness. Highlight unique or unusual interactions from this set of user's data analysis, using specific words since this summary will be incorporated with a broader report on the work an individual did. These interactions are only a segment of the whole investigation:\n\n{interactions_text}"
    # print("🌕 summarize segment:", prompt)
    if useGPT:
        return askGPT(prompt)
    else:
        return "This would be a summary. The words are easy to read with nice things to say. You May not enjoy it all but at least it is a nice length."

def summarize_all_segments(segment_summaries):
    """
    Summarizes interactions in a segment using ChatGPT.

    Parameters:
    segment_interactions (list): List of interactions in the segment.

    Returns:
    str: The summary of the segment.
    """
    interactions_text = "\n".join([str(summary) for summary in segment_summaries])
    prompt = f"Here are {segmentsPath} summaries from sections of a user's investigation of data. Please combine and summarize into an overarching, 500 character string that explains the main events, topics covered, and findings. Consider including reference numbers for which index/segment different information comes from:\n{interactions_text}"
    # print("🌕 summarize segment:", prompt)
    if useGPT:
        return askGPT(prompt)
    else:
        return "Overarching summary is now a bit longer and interesting but it refers to places like segment 3 and such."

def update_entities(entities, key, value):
    # Convert the key to lowercase for case-insensitive matching
    key = key.lower()
    
    # Mapping of keys to entity types
    # These mappings define how different keys should update the 'entities' dictionary
    cases = {
        "search": "Search",             # Maps "search" and "searches" to "Search"
        "searches": "Search",
        "topics": "Doc_open",           # Maps "topics" to "Doc_open"
        "concepts": "Highlights",       # Maps "concepts" to "Highlights"
        "people": "PersonEnt",          # Maps "people" and "persons" to "PersonEnt"
        "persons": "PersonEnt",
        "places": "GeoEnt",             # Maps "places" and "locations" to "GeoEnt"
        "locations": "GeoEnt",
        "dates": "Dates",               # Maps "dates" to "Dates"
        "document titles": "Doc_open"   # Maps "document titles" to "Doc_open"
    }

    # Check if the key is in the predefined mapping
    if key in cases:
        entity_key = cases[key]
        
        # Ensure value is always a list, even if it's a single value
        if not isinstance(value, list):
            value = [value]

        # Update entities dictionary based on entity_key
        if entity_key in entities:
            if isinstance(entities[entity_key], list):
                # If entity_key already exists and is a list, extend it with new values
                entities[entity_key].extend(value)
            else:
                # If entity_key exists but is not a list, convert it to a list and add new values
                entities[entity_key] = [entities[entity_key]] + value
        else:
            # If entity_key does not exist in entities, initialize it with the new values
            entities[entity_key] = value


def identify_entities(summary, attempts = 0, maxAttempts = 5):
    """
    Identifies entities in a summary.

    Parameters:
    summary (str): The summary text.

    Returns:
    dict: A dictionary of identified entities.
    """
    # Step 1: Construct a prompt
    # prompt = f"format your reply as a JSON object. Identify and list any of the 6 types of entities in the following text:\n{summary}\nEntities to look for: [search, topics, people, places, dates, document titles]. Make a dictionary with each of these Entities as keys and list any (or none) of the terms as values."

    prompt = f"Identify and make a short list of the following 4 kinds of information in the attached summary: [searches, highlights, people, places]. There should be less than 5 items in each list. Your response should be a JSON dictionary with arrays of string values. Make a dictionary with each entity type as keys and lists of exact terms as the values. If there is nothing applicable, you can provide an empty list for that entity type (e.g.,  ['']). Your response is valid JSON. Prioritize the most prominent and specific searches, highlights, people, and places the individual read about in the following summary:\n\n{summary}"

    default_entities = {
        "Search": [""],
        "Highlights": [""],
        "PersonEnt": [""],
        "GeoEnt": [""],
    }

    # Step 2: Use askGPT to get the response
    entities = {}
    if(useGPT):
        try:
            response = askGPT(prompt)
            structured_response = json.loads(response) #type: ignore
            print(structured_response, f"\033[32m{type(structured_response)}\033[0m")
            # Step 3: Parse the response to extract entities
            for key, value in structured_response.items():
                update_entities(entities, key, value)
        except TypeError as e:
            print(f"Uh oh: {e}")
        except json.decoder.JSONDecodeError as f:
            entities = default_entities            
            #try again so long as it's not too many attempts.
            # if attempts < maxAttempts :
            print(f"decode error This is not JSON - \033[31m{f}\033[0m::::{response}")
            #     attempts += 1
            #     entities = identify_entities(summary, attempts, maxAttempts)
            # else:

    else:
        entities = default_entities

    return entities

def fuzzy_highlight_entities(summary, entities, threshold=80):
    """
    Highlights entities in the summary text with HTML code.

    Parameters:
    summary (str): The summary text.
    entities (dict): A dictionary of entities to highlight.

    Returns:
    str: The summary text with highlighted entities.
    """
    words = summary.split()

    for entity_type, terms in entities.items():
        color = colors[entity_type]
        for term in terms:
            newTerm = str(term).replace(" ", "_").lower()

            # Find the best matches for the term in the summary
            matches = process.extract(term, words, limit=len(words))
            
            for match, score in matches: # type: ignore
                if score >= threshold:
                    highlighted_term = f"<span onmouseover=highlightSimilar('{newTerm}') onmouseout=unhighlightCards() class='descriptionTerm {entity_type}' style='color:{color}; font-weight:bold'>{match}</span>"
                    summary = summary.replace(match, highlighted_term)
    return summary

def highlight_entities(summary, entities):
    """
    Highlights entities in the summary text with HTML code.

    Parameters:
    summary (str): The summary text.
    entities (dict): A dictionary of entities to highlight.

    Returns:
    str: The summary text with highlighted entities.
    """
    for entity_type, terms in entities.items():
        color = colors[entity_type]
        for term in terms:
            noSpaceTerm = str(term).replace(" ", "_").lower()
            summary = summary.replace(term, f"<span onmouseover=highlightSimilar('" + noSpaceTerm +"" + "') onmouseout=unhighlightCards() class='descriptionTerm "+entity_type+"' style='color:" + color + "; font-weight:bold' >" + term + "</span>")
    return summary
   
def highlight_entities_case_insensitive(summary, entities):
    """
    Highlights entities in the summary text with HTML code.

    Parameters:
    summary (str): The summary text.
    entities (dict): A dictionary of entities to highlight.

    Returns:
    str: The summary text with highlighted entities.
    """
    def replace_with_highlight(match, newTerm, entity_type, color):
        original_term = match.group(0)
        return f"<span onmouseover=highlightSimilar('{newTerm}') onmouseout=unhighlightCards() class='descriptionTerm {entity_type}' style='color:{color}; font-weight:bold' >{original_term}</span>"
    
    for entity_type, terms in entities.items():
        color = colors[entity_type]
        for term in terms:
            newTerm = str(term).replace(" ", "_").lower()
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            summary = pattern.sub(lambda match: replace_with_highlight(match, newTerm, entity_type, color), summary)
    
    return summary

def assignSegment(interaction, ds, pid, segments, debug = False):
    #try to access the 'segment' property. Return the interaction if the property exists
    try:
        int(interaction["segment"])
        return interaction
    #if no property, then attempt to identify the appropriate segment.
    except KeyError:
        if debug: print("Found an event without a 'segment' property, trying to assign appropriate segment:")
        tCheck = int(interaction["time"])
        for i in range(int(segmentsPath)):
            start = segments[ds+pid+i]["start"]
            end = segments[ds+pid+i]["end"]
            if debug: print("--",interaction["interactionType"], start, tCheck, end)
            if start <= tCheck <= end:
                if debug: print(f"--> Found the correct segment number for interaction '{interaction["type"]}' at {interaction["time"]}")
                interaction.update({"segment":i})
                break
            elif (i + 1 == int(segmentsPath)):
                if debug: print("assigning the last segment for the interaction event:", int(segmentsPath)-1)
                interaction["segment"] = int(segmentsPath)-1
    return interaction


def main():
    # 1. Read the dataset into memory
    data = load_json_file(dataset_path)
    print(data.keys())

    interaction_logs = data["interactionLogs"] # keep this line for when you bring loops back in.
    segments = data["segments"]

    # Initialize a dictionary to hold interactions by segments
    segment_interactions = {i: [] for i in range(len(segments))}
    # print("🚀 ~ segment_interactions:", type(segment_interactions))

    # Iterate over interaction logs
    # for user in range(len(interaction_logs)):
    if True:
        user = 0
        # documents_path = parentDirectory+"/data/Dataset_"+str(user+1)+"/Documents/Documents_Dataset_"+str(user+1)+".json"
        # entities_path = parentDirectory+"/data/Dataset_"+str(user+1)+"/Documents/Entities_Dataset_"+str(user+1)+".json"
        # print("🚀 ~ documents_path:", documents_path)
        # tempdocs = load_json_file(documents_path)
        # docs = []
        
        # LLMStage = "01-summary/"
        # for doc in tempdocs:
        #     if useGPT:
        #         summaryString = askGPT('Please examine the content of this JSON record record and provide a 1 sentence summary of the content and a short list of the topics. Your response should have no additional characters or padding. return a json object with the form: {"summary":"Generate summary text here.","topics":["topic1","topic2","topic3"]}. Here is the record:\n\n'+str(doc))
        #     else:
        #         summaryString = '{"Summary":"This would be a summary from GPT", "topics":["one","two","three"]}'
        #     # Parse JSON string to dictionary
        #     summary = json.loads(str(summaryString))
        #     doc.update(summary)
        #     docs.append(doc)
        # save_json_to_file(docs, LLMPartialsDirectory+LLMStage+"documents"+str(user)+".json")

        LLMStage = "02-merging/"
        # tempPeepPlace = load_json_file(entities_path)
        # documents = merge_json(docs,tempPeepPlace)
        # save_json_to_file(documents, LLMPartialsDirectory+LLMStage+"documents"+str(user)+".json")
        documents = load_json_file(LLMPartialsDirectory+LLMStage+"documents"+str(user)+".json")

        # Iterate over each interaction of the user
        for interactions in interaction_logs[user]:
            tempset = []
            lastsegment = 0
            for interaction in interactions:
                ds = int(interaction["dataset"]) - 1
                pid = int(interaction["PID"]) - 1
                seg = assignSegment(interaction, ds, pid, segments)["segment"]
                #assign the interaction to a grouped set of interactions.
                
                if checkEventType(interaction):
                    if seg == lastsegment:
                        tempset.append(interaction)
                    else:
                        index = ds*int(participantCnt)*int(segmentsPath) + pid*int(segmentsPath) + seg - 1
                        # print(f"This event belongs to seg {seg}, ds {ds}, and pid {pid}, moving to the next segment: {index}")
                        # segment_interactions[index].append(interaction)
                        segment_interactions.update({index:tempset})
                        lastsegment = seg
                        tempset = [interaction]
                # Ensure the final segment is captured (in case this is the last interaction)
                final_index = ds * int(participantCnt) * int(segmentsPath) + pid * int(segmentsPath) + lastsegment
                segment_interactions.update({final_index: tempset})
    
        # Clean up and Add Context to the interactions
        for idx in range(len(segment_interactions)):
            cntr = 0
            for interaction in segment_interactions[idx]:
                interaction = addContextToInteraction(interaction,documents)
            cntr += 1
    LLMStage = "03-ContextInteractions/"
    save_json_to_file(segment_interactions,LLMPartialsDirectory+LLMStage+"Segmented_Context_interactions.json")
    # segment_interactions = load_json_file(LLMPartialsDirectory+LLMStage+"Segmented_Context_interactions.json")
    # print(len(segment_interactions))

    # Initialize a list to store overall summaries for each user
    overall_summaries = []

    # for user in range(len(interaction_logs)):
    if True: #
        user = 0
        user_summaries = []

        LLMStage = "/04-segmentSummaries/Dataset_"+str(user)+"/"
        for idx in range(len(segment_interactions)):
            print(f"-DS{user}-Summarizing segment_{idx}")
            segment = segment_interactions[idx]
            cleaned_interactions = [clean_interaction(interaction) for interaction in segment]
            summary = summarize_segment(cleaned_interactions)
            save_json_to_file(summary, LLMPartialsDirectory + LLMStage + "SegmentSummaries/segment_"+str(idx)+".json")
            entities = identify_entities(summary)
            save_json_to_file(entities, LLMPartialsDirectory + LLMStage + "SegmentEntities/segment_"+str(idx)+".json")
            highlighted_summary = highlight_entities(summary, entities)

            user_summaries.append(highlighted_summary)
        save_json_to_file(user_summaries, LLMPartialsDirectory + f"Highlighted_segment_summaries_DS_{str(user)}.json")

        # Summarize all segments for the user into an overall summary
        for person in range(int(participantCnt)):
            # person = 0
            segmentSummaries = []
            for chunk in range(int(segmentsPath)):
                # print(f"gathering chunk #{chunk+1}/{int(segmentsPath)} for final summary for user #{person}")
                segmentSummaries.append(user_summaries.pop(0))
             
            LLMStage = "05-superlativeSummaries/"
            overall_summary = summarize_all_segments(segmentSummaries)
            save_json_to_file(overall_summary, LLMPartialsDirectory + LLMStage + f"ds_{user}_p_{str(person)}.json")
            overall_entities = identify_entities(overall_summary)
            highlighted_overall_summary = highlight_entities(overall_summary, overall_entities)
            overall_summaries.append(highlighted_overall_summary)

    save_json_to_file(overall_summaries, LLMPartialsDirectory + f"LLM_superlative_summaries_{segmentsPath}.json")

    # LLMStage = "06-Combine/"
    universalCNTR = 0
    combined_data = {}

    # Adding superlatives.json to combined_data
    combined_data['superlatives'] = copy.deepcopy(overall_summaries)
    print("🚀 ~ combined_data:", len(combined_data["superlatives"]), type(combined_data))
    
    combined_data["segments"]={}
    # for dataset in range(3):
    if True:
        dataset = 0
        datasetSegments = load_json_file(LLMPartialsDirectory+f"Highlighted_segment_summaries_DS_{dataset}.json")
        for seg in range(len(datasetSegments)):
            segmentText = datasetSegments[seg]
            segmentNumber = (universalCNTR)%int(segmentsPath)
            #todo figure out the calculation for PID
            # pid = math.floor(universalCNTR/(int(segmentsPath)+int(participantCnt)))
            # print("🚀 ~ pid:", pid, segmentNumber, universalCNTR)
            combined_data["segments"][universalCNTR] = {
                "text" : segmentText,
                "segment" : segmentNumber,
                "ds" : dataset,
                # "pid" : pid
                }
            universalCNTR += 1 
    combined_data["segmentLength"] = universalCNTR
    # Step 3: Save combined_data to a JSON file (if needed)
    save_json_to_file(combined_data, parentDirectory + f"/interface/LLMManifest_{segmentsPath}.json")

# Call the final_todo function at the end of the main function
main()
