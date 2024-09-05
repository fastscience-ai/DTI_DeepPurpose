import numpy as np
import os


def top_k_ensemble(list_of_filenames):
    """
    Input: list of files named with sample_submission_*_*.csv
    Output: averaged value across the list of sample submission files
    """
    test = {i:0.0 for i in range(113)}
    for i in range(len(list_of_filenames)):
        file_in=open(list_of_filenames[i], "r")
        count = 0
        for line in file_in.readlines():
            if count>0:
                val = test[count-1]
                test[count-1] = val + float(line.split(",")[1])
            count = count+1
    n=float(len(list_of_filenames))
    for i in range(len(test)):
        test[i] = test[i]/n

    file_out = open("sample_submission_top_"+str(int(n))+".csv", "w")
    file_out.write("ID,IC50_nM\n")
    for i in range(len(test)):
        file_out.write("TEST_"+f"{i:03},"+str(test[i])+"\n")
    file_out.close()
    
def main():
    list_of_files=["sample_submission_MPNN_CNN_RNN.csv", "sample_submission_MPNN_AAC.csv" , "sample_submission_MPNN_CNN_RNN.csv"  , "sample_submission_MPNN_Transformer.csv", "sample_submission_MPNN_CNN.csv", "sample_submission_MPNN_ESPF.csv"]
    top_k_ensemble(list_of_files)

if __name__ == "__main__":
    main()



