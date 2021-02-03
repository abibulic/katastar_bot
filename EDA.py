import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def list_files(root_dir, ext='.txt'):
    file_list = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(ext):
                file_list.append(os.path.join(root, file).replace("\\","/"))
    return file_list


def main():
    line = 'Katastarska općina;Broj katastarske čestice;Adresa katastarske čestice;Površina katastarske čestice/m2;Posjedovni list;Način uporabe i zgrade + Površina/m2;Posjedovni list + Udio + Ime i prezime/Naziv + Adresa\n'

    file_path = 'D:/WORK/PROJECTS/katastar_bot/data/dataframes/'
    files = list_files(file_path)

    all_lines = []
    for file in files:
        try:
            f.close()
        except:
            print('there is no file to close!')
            
        f = open(file, 'r')
        lines = f.readlines()

        all_lines += lines

    for i, line in enumerate(all_lines):
        try:
            int(line.split(',')[0])
            ff.write(line)
        except:
            print('..')

    ff.close()
    return 0

def read_pandas()
    file_path = 'D:/WORK/PROJECTS/katastar_bot/data/dataframes/'

    data_categories = [
                    'kat_op', #'Katastarska općina',
                    'kat_num', #Broj katastarske čestice',
                    'kat_adresa', #'Adresa katastarske čestice',
                    'kat_area', #'Površina katastarske čestice/m2',
                    'vlas_list', #'Posjedovni list',
                    'uporaba', #'Način uporabe i zgrade + Površina/m2',
                    'names' #'Posjedovni list + Udio + Ime i prezime/Naziv + Adresa'
    ]

    data = pd.read_csv(f'{file_path}all_data.txt',
                   names=[
                        'kat_op', #'Katastarska općina',
                        'kat_num', #Broj katastarske čestice',
                        'kat_adresa', #'Adresa katastarske čestice',
                        'kat_area', #'Površina katastarske čestice/m2',
                        'vlas_list', #'Posjedovni list',
                        'uporaba', #'Način uporabe i zgrade + Površina/m2',
                        'names' #'Posjedovni list + Udio + Ime i prezime/Naziv + Adresa'
                       ],sep=';', encoding='ansi')

if __name__ == "__main__":
    read_pandas()
    