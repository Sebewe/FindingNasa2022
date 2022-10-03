from datetime import date
import os
from shutil import move
from pathlib import Path

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
