from sklearn.metrics import mean_squared_error
from DeepPurpose import utils, dataset
from DeepPurpose import DTI as models
import pandas as pd
import warnings
import torch
import os
import numpy as np
warnings.filterwarnings("ignore")
#This code is referred with https://github.com/kexinhuang12345/DeepPurpose/blob/master/Tutorial_1_DTI_Prediction.ipynb


def data_repreprocess(path_to_dataset, file_name, new_file_name):
    """
    Input: path and file_name to new_train_protein.csv which is generated by Seoyeon's code
    Output: new txt file with the same format of DeepPurpose
    """
    data = pd.read_csv(path_to_dataset+"/"+file_name)
    new_data = data[["Smiles", "Sequence", "pIC50"]]
    print(new_data)
    new_data.to_csv(path_to_dataset+"/"+new_file_name, sep=' ', index=False)
    # delete first row as it makes error
    file_in = open(path_to_dataset+"/"+new_file_name, "r")
    file_out = open(path_to_dataset+"/new_"+new_file_name, "w")
    count = 0
    for line in file_in.readlines():
       if count > 0:
           if len(line.split(" ")[2])>10:
               print(line)
           else:
               file_out.write(line)
           #try:
           #    score = float(line.split("\t")[2])
           #    file_out.write(line)
           #except:
           #    print(line)
           #    pass
       count=count+1
    file_in.close()
    file_out.close()


def test_with_our_testset(path_to_testset):
    """
    Input: path to our customs testset selected from Prof' Kim's lab.
    Output: list of drug, target, score
    """
    file_in = open(path_to_testset, "r")
    drug = []
    target = []
    score = []
    for line in file_in.readlines():
        try:
            drug.append(line.split("\t")[0])
            target.append(line.split("\t")[1])
            score.append(float(line.split("\t")[2]))
        except:
            print(line)
    return drug, target, score


def test_with_dacon_testset(path_to_testset):
    """
    Input: path to our customs testset selected from DACON competition
    Output: list of drug, target, score
    """
    sequence = {"CHEMBL3778": "MNKPITPSTYVRCLNVGLIRKLSDFIDPQEGWKKLAVAIKKPSGDDRYNQFHIRRFEALLQTGKSPTSELLFDWGTTNCTVGDLVDLLIQNEFFAPASLLLPDAVPKTANTLPSKEAITVQQKQMPFCDKDRTLMTPVQNLEQSYMPPDSSSPENKSLEVSDTRFHSFSFYELKNVTNNFDERPISVGGNKMGEGGFGVVYKGYVNNTTVAVKKLAAMVDITTEELKQQFDQEIKVMAKCQHENLVELLGFSSDGDDLCLVYVYMPNGSLLDRLSCLDGTPPLSWHMRCKIAQGAANGINFLHENHHIHRDIKSANILLDEAFTAKISDFGLARASEKFAQTVMTSRIVGTTAYMAPEALRGEITPKSDIYSFGVVLLEIITGLPAVDEHREPQLLLDIKEEIEDEEKTIEDYIDKKMNDADSTSVEAMYSVASQCLHEKKNKRPDIKKVQQLLQEMTAS"}

    file_in = open(path_to_testset, "r")
    drug = []
    target = []
    score = []
    for line in file_in.readlines():
        drug.append(line.split(",")[1])
        target.append(sequence["CHEMBL3778"]) #protein target is always same here
        score.append(0.0) # We don't know the score, lets just say 0.0
    return drug, target, score


def pic50_to_ic50_nM(pic50):
    """
    Convert pIC50 to IC50 in nanomolar (nM).

    Parameters:
    pic50 (float): The pIC50 value.

    Returns:
    float: The IC50 value in nanomolar (nM).
    """
    ic50_nM = 10.0**(9.0 - pic50)
    return ic50_nM

def normalized_rmse(y_true, y_pred, norm_type='range'):
    """
    Compute normalized RMSE.
    
    Parameters:
    y_true (array): Actual values.
    y_pred (array): Predicted values.
    norm_type (str): Type of normalization ('range' or 'mean'). Defaults to 'range'.
    
    Returns:
    float: Normalized RMSE.
    """
    # Calculate RMSE
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # Normalize based on the selected method
    if norm_type == 'range':
        norm_value = np.max(y_true) - np.min(y_true)
    elif norm_type == 'mean':
        norm_value = np.mean(y_true)
    else:
        raise ValueError("Invalid norm_type. Choose 'range' or 'mean'.")
    
    # Calculate normalized RMSE
    nrmse = rmse / norm_value
    return nrmse

def error_metrics(pic50_gt, pic50_pr):
    absolute_error_pic50 = [ np.abs(pic50_gt[i]-pic50_pr[i])   for i in range(len(pic50_gt))]
    correction_ratio = sum([1 if x > 0.5 or x == 0.5 else 0 for x in absolute_error_pic50])/float(len(absolute_error_pic50))
  
    pic50_nrmse = normalized_rmse(np.asarray(pic50_gt), np.asarray(pic50_pr))

    ic50_gt = [pic50_to_ic50_nM(val) for val in pic50_gt]
    ic50_pr = [pic50_to_ic50_nM(val) for val in pic50_pr]
    ic50_nrmse = normalized_rmse(np.asarray(ic50_gt), np.asarray(ic50_pr))
    dacon_score = 0.5*(1-min(1,ic50_nrmse))+0.5*correction_ratio
    return pic50_nrmse, ic50_nrmse, dacon_score

def make_dacon_sample_submission(y_pred_dacon, drug_encoding, target_encoding):
    file_out = open("sample_submission_"+drug_encoding+"_"+target_encoding+".csv", "w")
    file_out.write("ID,IC50_nM\n")
    for i in range(len(y_pred_dacon)):
        file_out.write("TEST_"+f"{i:03},"+str(pic50_to_ic50_nM(y_pred_dacon[i]))+"\n")
    file_out.close()


def main():
    #Convert data format from our data to DeepPurpose
    data_repreprocess("./dataset", "new_train_protein.csv", "dti_train.txt")
    data_repreprocess("./dataset", "new_test_protein.csv", "dti_test.txt")
    #Data read
    X_drugs_train, X_targets_train, y_train = dataset.read_file_training_dataset_drug_target_pairs('./dataset/new_dti_train.txt')
    X_drugs_test, X_targets_test, y_test = dataset.read_file_training_dataset_drug_target_pairs('./dataset/new_dti_test.txt')
    #Am I reading the correct data?
    print('Drug 1: ' + X_drugs_test[0])
    print('Target 1: ' + X_targets_test[0])
    print('Score 1: ' + str(y_test[0]))

    fout=open("DTI_results_soo.csv", "w")
    drug_encoding_list = ["MPNN", "ESPF", "Transformer", "CNN", "CNN_RNN", "Morgan", "Pubchem", "rdkit_2d_normalized", "ErG" ]
    target_encoding_list = ["ESPF", "CNN", "CNN_RNN", "Transformer", "AAC", "PseudoAAC", "Conjoint_triad", "Quasi-seq"]

    for drug_encoding in drug_encoding_list:
        fout_drug = open("DTI_results_"+str(drug_encoding)+".csv","w")
        for target_encoding in target_encoding_list:
            print(drug_encoding, target_encoding)
            # data split (lets just use their function for now)
            train= utils.data_process(X_drugs_train, X_targets_train, y_train, drug_encoding, target_encoding,split_method='no_split')
            val  = utils.data_process(X_drugs_test, X_targets_test, y_test, drug_encoding, target_encoding,split_method='no_split') 
            test = utils.data_process(X_drugs_test, X_targets_test, y_test, drug_encoding, target_encoding,split_method='no_split')   
            #Define model
            config = utils.generate_config(drug_encoding = drug_encoding, 
                                 target_encoding = target_encoding, 
                                 cls_hidden_dims = [1024,1024,512], 
                                 train_epoch = 100, 
                                 LR = 0.005, 
                                 batch_size = 128,
                                 hidden_dim_drug = 128,
                                 mpnn_hidden_size = 128,
                                 mpnn_depth = 3, 
                                 cnn_target_filters = [32,64,96],
                                 cnn_target_kernels = [4,8,12]
                                )
            model = models.model_initialize(**config)
            #Train model
            model.train(train, val, test)
            #Test model with our custom data
            drug, target, y = test_with_our_testset("./dataset/new_dti_test.txt")
            X_pred = utils.data_process(drug, target, y, 
                                        drug_encoding, target_encoding, 
                                        split_method='no_split')
            y_pred_custom = model.predict(X_pred)
            pic50_nrmse, ic50_nrmse, dacon_score = error_metrics(y, y_pred_custom)
            print("DRUG ENCODING:", drug_encoding, "TARGET ENCODING:", target_encoding ,"PIC_50 Normalized RMSE:", pic50_nrmse,"IC_50_nM Normalized RMSE:", ic50_nrmse,"DACON Score:", dacon_score)
            fout.write("DRUG ENCODING:,"+str(drug_encoding)+",TARGET ENCODING:,"+str(target_encoding) +",PIC_50 Normalized RMSE:,"+str(pic50_nrmse)+",IC_50_nM Normalized RMSE:,"+str(ic50_nrmse)+",DACON Score:,"+str(dacon_score)+"\n")
            fout_drug.write("DRUG ENCODING:,"+str(drug_encoding)+",TARGET ENCODING:,"+str(target_encoding) +",PIC_50 Normalized RMSE:,"+str(pic50_nrmse)+",IC_50_nM Normalized RMSE:,"+str(ic50_nrmse)+",DACON Score:,"+str(dacon_score)+"\n")

            #Test model with the dacon dat
            # [NOTE!!] you should delete the first row of test.csva
            drug, target, score = test_with_dacon_testset("./dataset/test.csv")
            X_pred = utils.data_process(drug, target, score,
                                        drug_encoding, target_encoding,
                                        split_method='no_split')
            y_pred_dacon = model.predict(X_pred)
            make_dacon_sample_submission(y_pred_dacon,drug_encoding, target_encoding)
        fout_drug.close()
    fout.close()

if __name__ == "__main__":

    device = torch.device( "cpu")
    main()
