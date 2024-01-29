import re
import uuid
#import simplejson as json
import pandas as pd
import os
import shutil

# On lit le ficier *.gw converti en *.txt
with open('base.txt', 'rt') as myfile:
  fichier = myfile.read()

# Regular expression to match lines that start with 'fam'
pattern = r"^fam .*?$"
matching_lines = re.findall(pattern, fichier, flags=re.MULTILINE)
matching_lines_with_uuid = [line + " 'org_UUID':'" + str(uuid.uuid4()) + "'" for line in matching_lines]
cleaned_text = '\n'.join(matching_lines_with_uuid )

#### REMOVE ANY URL
pattern = r'https?://[\w.-]+/\w*\?[\w=&+?-]*(?=\s|$)'
cleaned_text = re.sub(pattern, "url ", cleaned_text, flags=re.MULTILINE)

# Regular expression to match 'fam ... +' and split while keeping the UUID
pattern = r"(fam )(.+)(\+)(.+?)('org_UUID':'.+?)$"
cleaned_text = re.sub(pattern, r"\5 - \2\n\5 - \4", cleaned_text, flags=re.MULTILINE)

## SUPPRESSION DOUBLE ESPACE
pattern = r"[ ]{2,}"
cleaned_text = re.sub(pattern, " ", cleaned_text, flags=re.MULTILINE)

#### supression date de mariage
pattern = r"\- [~?<>]?\d{0,2}?/?\d{0,2}?/?\d{4}? "
cleaned_text = re.sub(pattern, "- ", cleaned_text, flags=re.MULTILINE)

#### supression lieu de mariage
pattern = r"#mp \S+ "
cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)

#### supression lieu de mariage
pattern = r"#nm "
cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)

#### supression lieu de mariage
pattern = r"#noment "
cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)

#### supression source de mariage
pattern = r"#ms \S+ "
cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)

pattern = r"[\?fm]{2} "
cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)


#### supression date de séparation
pattern = r"\-[~?<>]?(\d{0,2}?/?\d{0,2}?/?\d{4}?)? "
cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)

print(cleaned_text)
print("----------------")
print(len(cleaned_text.split("\n")))
print("----------------")
import csv

# Split the cleaned text into lines
lines = cleaned_text.split('\n')

# Open a CSV file to write the lines
with open('data_regex.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)

    # Write each line as a row in the CSV file
    for line in lines:
        csvwriter.writerow([line])