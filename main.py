import string
import sys
import os
from HTMLLexer import HTMLLexer
import matplotlib.pyplot as plt
import time
import shutil
import psutil

if __name__ == "__main__":

    m = HTMLLexer()
    m.build()

    directory = os.path.join(os.getcwd(), "./static/files")
    files = os.listdir(directory)


    #delete and then create the directory for our tokenized files
    if os.path.exists('output'):
        shutil.rmtree('output')
    if not os.path.exists('output'):
        os.makedirs('output')

    #for elapsed time
    elapsed_time = []
    start = time.time()

    #for cpu time
    p = psutil.Process()
    cpu_time = []
    cpu_time.append(0.00)

    #For Map File
    docID = 0
    mapFile = os.path.join(os.getcwd(), "output/map.txt")
    with open(mapFile, 'w') as f:

        #Loop over all files and tokenize them
        for file in files:
            #write the tokens

            if file.endswith(".html"):
                inputFile = os.path.join(directory,file)
                # outputFile = os.path.join(os.getcwd(), "output/" + str(file)[:-5] + "_tokenized.txt")

                m.tokenizeFile(inputFile, docID)
                end = time.time()

                elapsed_time.append(end - start)
                cpu_time.append(cpu_time[-1] + sum(p.cpu_times()[:2]))

            #write the mapFile
                f.write("%-16s\n" % (file))
                docID+= 1

    # Passing total number of documents as docID+1
    m.finish2(docID+1)


    #plot the time charts
    plt.plot(range(len(elapsed_time)), elapsed_time)
    plt.title('Tokenization Elapsed Time')
    plt.xlabel('File Number')
    plt.ylabel('Elapsed Time (seconds)')
    plt.savefig("Elapsed.png")

    plt.plot(range(len(cpu_time)), cpu_time)
    plt.title('Tokenization CPU Time')
    plt.xlabel('File Number')
    plt.ylabel('CPU Time (ms)')
    plt.savefig("CPU.png")



