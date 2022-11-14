import os
import json

# path = os.getcwd()+"/code/ProvSegments/Pandajam-raw-logs-from-las/ds4-testset/"
path = os.getcwd()+"/code/ProvSegments/Pandajam-raw-logs-from-las/processed_json_20220715_apollo_fixes_2/"
# Get the list of files in directory
files = os.listdir(path)
files = [f for f in files if os.path.isfile(path+'/'+f)] #Filtering only the files.



def merge_JsonFiles(dir, filename):
    result = list()
    for f1 in filename:
        with open(dir+f1, 'r') as infile:
            content = json.load(infile)
            #TODO: clean up the file content so it does not contain "spk_0" or [0:0:0] things.
            #TODO: Consider replacing all the "spk_0" with the first linked speaker so it shows the actual names more often.
            content["contents"] = content.pop("transcriptBySpeaker")
            content["id"] = content.pop("audioURL")
            result.append(content)

    with open(dir + '../../Dataset_4/Documents/Documents_Dataset_4.json', 'w') as output_file:
        json.dump(result, output_file)


merge_JsonFiles(path, files)