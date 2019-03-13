import csv

def readCsvSafe(fileName: str, keepHeader = False):
    try:
        with open(fileName) as f:
            print("Reading %s " % f.name)
            csvData = list(csv.reader(x.replace('\0', '') for x in f))
            # csvData = list(csv.reader(f))
            return csvData if keepHeader else csvData[1:]
    except FileNotFoundError as e:
        print("Could not find file %s" % fileName)

