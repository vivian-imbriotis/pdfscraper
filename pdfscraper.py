import pdftotext as p2t
import re
import numpy as np
import sys, os


def scrape_pdf(path, printing = False):
    with open(path, "rb") as file:
        pdf = p2t.PDF(file)

    text = pdf[0] #the first page, since there is only one page
    text = text.splitlines()
    lines = []
    for line in text:
        line = line.strip()
        line = re.sub(" +", " ", line)
        if printing:
            print(line)
        lines.append(line)
    return lines



def fetch_acuity_array(lines,eye):
    field_text = lines[14:18] + lines[19:23] #The lines containing the acuity matrix
    field_ints = []
    if eye == "left":
        for row in field_text:
            row = row.split(" ")
            int_row = []
            for i in range((9-len(row))//2):
                int_row.append(0) #left padding
            for value in row:
                try:
                    int_row.append(int(value))
                except ValueError:
                    if value == "<0":
                        int_row.append(0)
                    else:
                        raise
            while len(int_row) < 9:
                int_row.append(0) #right padding
            field_ints.append(int_row)
    elif eye == "right":
        for row in field_text:
            row = row.split(" ")
            int_row = []
            for i in range((9-len(row))//2):
                int_row.append(0) #left padding
            if len(row)!=9:
                int_row.append(0) #more left padding
            for value in row:
                try:
                    int_row.append(int(value))
                except ValueError:
                    if value == "<0":
                        int_row.append(0)
                    else:
                        raise
            while len(int_row) < 9:
                int_row.append(0) #right padding
            field_ints.append(int_row)
    else:
        raise ValueError("eye argument must be either \"left\" or \"right\"")
    return np.asarray(field_ints)


class EyeExam:
    def __init__(self,path_to_pdf):
        lines = scrape_pdf(path_to_pdf, printing = False)
        self.name = lines[0][lines[0].index(" ")+1:]
        self.id = lines[3].split(" ")[2]
        self.fixation_monitor = lines[7].split(" ")[2]
        self.fixation_target = lines[8].split(" ")[2]
        self.age = lines[9].split(" ")[-1]
        if lines[6][0:2] == "OS":
            self.eye = "left"
        elif lines[6][0:2] == "OD":
            self.eye = "right"  
        else:
            raise LookupError("Laterality encoding (\"OS\" or \"OD\")"
                              + "not found in expected location")
        self.acuity_array = fetch_acuity_array(lines,self.eye)
    def __call__(self):
        return self.acuity_array
    def __repr__(self):
        return "Patient %s's %s eye data" %(self.id, self.eye)
    def __str__(self):
        string_out = (("Patient ID: %s\n" %self.id)
                      + ("Patient Age: %s\n" %self.age)
                      + ("Patient Name: %s\n\n"%self.name)
                      + "Visual fields of %s eye\n"%self.eye
                      + self.acuity_array.__str__()
                      +"\n")
        return string_out
        

if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Provide at least one pdf as an command line argument\n"
                         + "Example usage:\n"
                         +"> python3 pdfscraper.py /path/to/ptsfile")
        exit(0)
    for path in sys.argv[1:]:
        try:
            print(EyeExam(path))
        except IsADirectoryError:
            print("Scrapting directory content...")
            for file in os.listdir(path):
                print(EyeExam(os.path.join(path,file)))
