# Brett's Provenance Visualization Tool

## Visualization Design

##### Table of Contents  
[Headers](#headers)  
[Emphasis](#emphasis)  
...snip...    
<a name="headers"/>
   
### Overview
Each segment is represented by a card with a unique segment number. A lightblue bar represents the timeline for the entire segment, with a dark blue block showing the relative start and end times for the segment. The length of this bar encodes the duration of the segment.
Below is a timeline of all actions in the segment to show actions in context to one another.
A textual summary of important actions in the segment is provided.
Key information about searching, note taking, highlighting, and document opening is included. Bars showing the relative frequency of each action are shown for each segment. A "Total" activity bar shows how much of the total activity among all segments occurs in the individual segment.

### Zoom and Filter
A control panel is present to load different participant data and toggle between a detailed and simple view of each summary. The detailed view shows the timeline of actions, as well as allows users to edit (merge/separate) segments. The control panel also allows users to save the modified JSON with their modified segments and the SVG images for all cards.

While in the detailed view, clicking and dragging on the light grey bar below the segment timeline allows selection of a sub-segment. Clicking the "Create from Selection" button will create up to three new segments (data before the selected time, the selected time, data after the selected time). If the resulting segments outside of the selection are short in duration (<5s) or the user clicks near the beginning or end of the segment, they will be grouped back into the selection. Arrow buttons on either side of the timeline will adjoin the segment with the previous or next segment.

### Details on Demand
Hovering over the timeline shows time and action details.
Colored text can be hovered to show the full text.
Hovering over each bar/icon displays all the interactions of the type with frequencies if the action occured mutliple times.

## Editing Segments
### Preprocessing
All relevent files are in the "code" folder.

The python script "provenance.py" conducts preprocessing on the "Segmentation" and "User Interaction" folders in each "code\ProvSegments\Dataset_X" folder. 
It converts segment csv files into json and merges all user interaction json into a single file for use with d3.

The python script requires an argument to run and its output piped to a json file. The argument specifies whether a merging proceedure is to be conducted to reduce the number of segments. The merging proceedure naively merges segments >1/24th the total time with an adjacent neighbor segment.

To NOT merge (recomemended):
```
python provenance.py 0 > vis.json
```

To merge:
```
python provenance.py 1 > vis.json
```

### Adding New Segments


To add new files:

**1)** New segment files must have the following format and the same file names as the orginal segments in "Dataset_X/Segmentation":
```
ID  start end length (sec)
0 0 112.7 112.7
1 112.7 438.9 326.2
2 438.9 586.1 147.2
3 586.1 590.8 4.7
4 590.8 636.6 45.8
...
```

**2)** Copy the old segments in the "Segmentation" folder somewhere for safekeeping.

**3)** Replace segments in the "Segmentation" folder with new files made in **1)**.

**3)** Run provenance.py again.

### Running the Visualization

**1)** Run localserver.bat.

**2)** Go to [http://localhost:8080/index.html](http://localhost:8080/index.html).
