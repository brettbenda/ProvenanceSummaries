# Read me

I want to remind myself how I was running these functions. They are mostly manual, but I've removed many more steps.

## Convert PJ data to match other Datasets

1. Open Raw PJ log in Excel
2. Apply a Data Filter to whole sheet
3. filter away all text that is not black (only keep events logged by the system)
4. Now open file that helps to extract all the keys and values (`formulasforExtractingDetails.xlsx`)
5. Copy formulas into rows and apply across whole sheet.
6. Now upload the file to a excel to JSON converter and the file is ready for translation.
7. Adjust the `translate-actions.py` file to translate the file you want, and then it should be ready for the system.

## Segmenting and NER

Next is all the things for Segmentation and NER... but at the time of writing, this has not be finalized.

That should be it.
