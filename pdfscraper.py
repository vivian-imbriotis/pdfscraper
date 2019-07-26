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
    #The lines containing the acuity matrix
    field_text = lines[14:18] + lines[19:23]
    #This variable is going to be a list of lists
    #that will be converted into a ndarray-type
    field_ints = []
    if eye == "left":
        for row in field_text:
            row = row.split(" ")
            int_row = []
            for i in range((9-len(row))//2):
                int_row.append(0) #left padding with 0
            for value in row:
                try:
                    int_row.append(int(value))
                except ValueError:
                    if value == "<0":
                        int_row.append(0)
                    else:
                        raise
            while len(int_row) < 9:
                int_row.append(0) #right padding with 0
            field_ints.append(int_row)
    elif eye == "right":
        for row in field_text:
            row = row.split(" ")
            int_row = []
            for i in range((9-len(row))//2):
                int_row.append(0) #left padding with 0
            if len(row)!=9:
                int_row.append(0) #more left padding with 0
            for value in row:
                try:
                    int_row.append(int(value))
                except ValueError:
                    if value == "<0":
                        int_row.append(0)
                    else:
                        raise
            while len(int_row) < 9:
                int_row.append(0) #right padding with 0
            field_ints.append(int_row)
    else:
        raise ValueError("eye argument must be either \"left\" or \"right\"")
    return np.asarray(field_ints)


class EyeExam:
    def __init__(self,path_to_pdf):
        lines = scrape_pdf(path_to_pdf, printing = False)
        #First, we extract the identifying infomation
        self.name = lines[0][lines[0].index(" ")+1:]
        if "." in self.name:
            self.last_name = self.name.split(".")[0].lower().capitalize()
            self.first_name = self.name.split(".")[1][0:-1].lower().capitalize()
        else:
            self.last_name,self.first_name = self.name.split(", ")
            self.last_name, self.first_name = self.last_name.lower().capitalize(), self.first_name.lower().capitalize()
        self.id = lines[3].split(" ")[2]
        self.age = int(lines[9].split(" ")[-1])
        #Next, quality control parametes
        self.fixation_monitor = lines[7].split(" ")[2]
        self.fixation_target = lines[8].split(" ")[2]
        self.fixation_losses = lines[9].split(" ")[2]
        self.false_pos_errors = lines[10][
            lines[10].index(":")+2:lines[10].index("%")+1]
        self.false_neg_errors = lines[11][
            lines[11].index(":")+2:lines[11].index("%")+1]
        self.test_duration = lines[12][15:20]
        self.forvea = lines[13][7:]
        #Next, assessment details
        self.ght = lines[29].split(": ")[1]
        self.vfi = lines[32].split(": ")[1]
        self.md = lines[33].split("MD: ")[1]
        self.md = self.md[0:self.md.index("B")+1]
        self.psd = lines[34].split(": ")[1]
        self.psd = self.psd[0:self.psd.index("B")+1]
        #Good practice to do error checking when fetching which eye was examined
        #since {left, right} is the complete set of possibilites...
        if lines[6][0:2] == "OS":
            self.eye = "left"
        elif lines[6][0:2] == "OD":
            self.eye = "right"  
        else:
            raise LookupError("Laterality encoding (\"OS\" or \"OD\")"
                              + "not found in expected location")
        #Finally, we fetch the actual data from the visual field matrix
        #as a numpy array (chosen because they're portable, work with
        #tensorflow and pytorch, etc)
        self.acuity_array = fetch_acuity_array(lines,self.eye)
    def __call__(self):
        return self.acuity_array
    def __repr__(self):
        return "%s's %s eye" %(self.last_name, self.eye)
    def __str__(self):
        string_out = (("Patient ID: %s\n" %self.id)
                      + ("Patient Age: %s\n" %self.age)
                      + ("Patient Name: %s\n\n"%self.name)
                      + "Visual fields of %s eye\n"%self.eye
                      + self.acuity_array.__str__()
                      +"\n")
        return string_out
    def print_detailed(self):
        for key in self.__dict__:
            print("%s: %s"%(key,self.__dict__[key]))


def recursive_scrape_pdfs(path):
    """
     Recursively scrape the contents of the path for pdfs
    \n:rtype: a list of EyeExam class instances
    """
    lis = []
    for file in os.listdir(path):
        if file[-4:] == ".pdf":
            lis.append(EyeExam(os.path.join(path,file)))
        elif os.path.isdir(file):
            lis.join(recursive_scrape_pdfs(os.path.join(path,file)))
    return lis

if __name__ == "__main__":
    if len(sys.argv)<2:
        print("Provide at least one pdf as an command line argument\n"
                         + "Example usage:\n"
                         +"> python3 pdfscraper.py /path/to/ptsfile")
        exit(0)
    for path in sys.argv[1:]:
        print(recursive_scrape_pdfs(path))
