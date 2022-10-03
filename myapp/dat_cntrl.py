import transformers
from transformers import PegasusForConditionalGeneration
from transformers import PegasusTokenizer
from pdfminer.high_level import extract_text
import pytextrank
from keybert import KeyBERT
import spacy.cli
import re
from time import sleep
from datetime import date
import os
from shutil import move
from pathlib import Path


def get_text(filepath):
    text = extract_text(filepath)
    countlines = lambda txt: txt.count('\n')
    print(f"linecount: {countlines(text)}, charcount: {len(text)}")
    return text

def get_abstract_sum(text: str, pegasus_tokenizer, pegasus_model):
    tokens = pegasus_tokenizer(text, truncation=True, padding="longest",
    return_tensors="pt", max_length=450, min_length=300)

    encoded_summary = pegasus_model.generate(**tokens)

    decoded_summary = pegasus_tokenizer.decode(
        encoded_summary[0],
        skip_special_tokens=True)

    return decoded_summary

def get_extract_sum(text: str, spacy_model):
    doc = spacy_model(text)
    extract_text = ""
    for i in doc._.textrank.summary(limit_sentences=5):
        extract_text += str(i)

    return extract_text

def get_keywords(text: str, keybert_model):
    return keybert_model.extract_keywords(text)

def cleanup(text: str):
    return re.sub(r"[^a-zA-Z0-9 ]", "", text)

def correct_files():
    BASE_DIR = '/opt/bitnami/yoink/media/documents/'
    #get files
    today = date.today()
    year, month, day = today.year, today.month, today.day
    fix = lambda num: str(num) if num >= 10 else "0"+str(num)
    year, month, day = fix(year), fix(month), fix(day)
    file_dir = BASE_DIR+f"{year}/{month}/{day}/"
    files = os.listdir(file_dir)
    if len(files) == 0: # if no files, return no files (:
        return None
    #put them into to-process
    TO_PROCESS_DIR = '/opt/bitnami/yoink/myapp/op_files/to_process/'
    for file in files:
        new_file = Path(TO_PROCESS_DIR+file)
        new_file.touch()
        move(file_dir + file, TO_PROCESS_DIR+file)

    return files #return first file found

def get_file():
    TO_PROCESS_DIR = '/opt/bitnami/yoink/myapp/op_files/to_process/'
    corrected = correct_files()
    if corrected:
        return TO_PROCESS_DIR+corrected[0]
    to_process = os.listdir(TO_PROCESS_DIR)
    if to_process:
        return TO_PROCESS_DIR+to_process[0]
    return None

def reformat_keywords(kwds):
    kwds = [('aperture', 0.51), ('frequency', 0.3954), ('frequencies', 0.3948), 
        ('instrument', 0.3859), ('coherence', 0.2686)]
    out_str = ''
    for kw in kwds:
        out_str += (f"Keyword: {kw[0]}; Calculated Relevance: {round(kw[1]*100, 2)}% \n")
    print(out_str)

def upload_file(file, abstract_sum, keywords):
    BASE_DIR = '/opt/bitnami/yoink/media/documents/processed'
    file_name = file.split('/')[-1]
    keywords_str = reformat_keywords(keywords)
    with open(BASE_DIR+file_name, 'w+'):
        file.write('Summary')
        file.write()
        file.write(abstract_sum)
        file.write()
        file.write()
        file.write()
        file.write('Keywords and Relevance')
        file.write()
        file.write(keywords_str)

def init():
    print("\n Starting Init \n")
    spacy.cli.download("en_core_web_lg")
    keybert_model = KeyBERT()

    model_name = "google/pegasus-xsum"
    pegasus_tokenizer = PegasusTokenizer.from_pretrained(model_name)
    pegasus_model = PegasusForConditionalGeneration.from_pretrained(model_name)

    spacy_model = spacy.load("en_core_web_lg")
    spacy_model.add_pipe("textrank") #previous nlp
    print("\n Init Completed :) \n")

    return {
        'keybert_model': keybert_model,
        'pegasus_tokenkizer': pegasus_tokenizer,
        'pegasus_model': pegasus_model,
        'spacy_model': spacy_model,
    }

if __name__ == "__main__":
    preloaded = init()
    BASE_DIR = '/opt/bitnami/yoink/myapp/op_files/'
    while True:
        file = get_file()
        if not file:
            sleep(5)
            continue
        #process first file found
        print(f"processing file \'{file}\' . . .")
        text = get_text(file)
        extract_sum = get_extract_sum(text, preloaded['spacy_model'])
        abstract_sum = cleanup(get_abstract_sum(extract_sum,
                                                preloaded['pegasus_tokenizer'],
                                                preloaded['pegasus_model']))
        keywords = get_keywords(text, preloaded['keybert_model'])

        #store processed data
        upload_file(file, abstract_sum, keywords)
