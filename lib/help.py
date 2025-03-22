# helper functions

import uproot
import numpy as np
import os
import time


# ask user for runs you would like to include
def get_runs_from_user():

    runs = []
    which_option = input("Read from a list (runs.list) or enter the runs manually?\nType '1' for the list, type '2' for manual submission:   ")

    if which_option == '1':
        try:
            with open('runs.list', 'r') as file:
                for line in file:
                    run = line.strip()
                    if run:  # ensure the line is not empty
                        runs.append(run)
            print("Runs added from runs.list")
        except FileNotFoundError:
            print("\nError: 'runs.list' file not found. Please create the list file and re-run the script.\n")
            exit()
    
    elif which_option == '2':
        print("Enter the runs you want to include. Type 'done' when you are finished.")
        while True:
            user_input = input("Enter run number: ")
            if user_input.lower() == 'done':
                break
            runs.append(user_input)

    else:
        print("\nError: please type '1' or '2'! Exiting...\n")
        exit()

    return runs


# check if there isn't RawData for any of the runs and omit that run from the list
def is_there_raw(runs_to_run_user, raw_path):
    temp_runs = []
    for i in range(len(runs_to_run_user)):
        if os.path.isdir(raw_path + runs_to_run_user[i] + '/'):
            temp_runs.append(runs_to_run_user[i])
        else:
            print('Run ' + runs_to_run_user[i] + ' does not have any RAWData!!! Removing from the list')
    return temp_runs


# run BeamFetcherV2 toolchain
def beamfetcher(run, step_size, raw_path, app_path, pwd_path, singularity, beamfetcher_path):

    os.system('rm beam.list')
    os.system('echo "' + run + '" >> beam.list')
    
    # does the run already have a beamfetcher file?
    exists = os.path.isfile(beamfetcher_path + 'beamfetcher_' + run + '.root')
    
    if exists == False:

        raw_dir = raw_path + run + "/"

        # temporary storage for created beamfetcher files
        os.system('mkdir -p ' + app_path + run)
        
        # Get the list of raw files and how many
        raw_files = [file for file in os.listdir(raw_dir) if file.startswith("RAWData")]
        num_raw_files = len(raw_files)

        if num_raw_files <= step_size:
            start_indices = ['0']; end_indices = [str(num_raw_files - 1)]
        else:
            start_indices = ['0']
            end_indices = []
            for i in range(step_size, num_raw_files, step_size):
                start_indices.append(str(i))
                end_indices.append(str(i - 1))
            end_indices.append(str(num_raw_files - 1))

        print('\n' + run + ' has ' + str(int(end_indices[-1])+1) + ' part files. Executing script now...')
        print('\nSteps to run:')
        print(start_indices, end_indices)      # lists of starting part file and ending part file
        time.sleep(1)

        for i in range(len(start_indices)):
            print('\nRun ' + run + '  parts ' + start_indices[i] + '-' + end_indices[i])
            print('***********************************************************\n')
            os.system('sh lib/run_beamfetcher.sh ' + start_indices[i] + ' ' + end_indices[i] + ' ' + app_path + ' ' + pwd_path + ' ' + raw_path + ' ' + singularity)
            time.sleep(1)

            # verify the file executed and there wasn't a toolchain crash (it will be very small if it failed < 5KB)
            # TODO - should probably add an exception if its a single part file
            # For now, re-run once
            size = os.path.getsize(app_path + 'beamfetcher_tree.root')
            if size < 5:   # smaller than 5KB - for now, just re-run once
                print('\nbeamfetcher file just produced is less than 5 KB - there must have been a crash')
                print('\nrerunning....')
                os.system('sh lib/run_beamfetcher.sh ' + start_indices[i] + ' ' + end_indices[i] + ' ' + app_path + ' ' + pwd_path + ' ' + raw_path + ' ' + singularity)
            else:
                print('\nFile looks good (over 5KB). Proceeding to the next one...')

            time.sleep(1)
            os.system('cp ' + app_path + 'beamfetcher_tree.root ' + app_path + run + '/beamfetcher_' + run + '_p' + start_indices[i] + '_' + end_indices[i] + '.root')
            time.sleep(1)
            os.system('rm ' + app_path + 'beamfetcher_tree.root')
            time.sleep(1)

        print('\nMerging beam files...\n')
        os.system('sh lib/merge_it.sh ' + singularity + ' ' + app_path + ' ' + run + ' ' + 'beamfetcher')
        time.sleep(1)
        
        print('\nTransferring beam file...\n')
        os.system('cp beamfetcher_' + run + '.root ' + beamfetcher_path + '.')
        time.sleep(1)
        os.system('ls -lrth ' + beamfetcher_path + 'beamfetcher_' + run + '.root')
        os.system('rm -rf ' + app_path + run + '/')     # folder to hold the segmented beamfetcher root files
        os.system('rm beamfetcher_' + run + '.root')

    else:
        print('BeamFetcher file present in /persistent for ' + run + ', moving on...\n')

    return


# grab POT (both upstream and downstream)
def POT(run, beamfetcher_path):

    pot_875 = 0     # downstream toroid
    pot_860 = 0     # upstream toroid

    # beamfetcher_<RUN>.root
    root = uproot.open(beamfetcher_path + 'beamfetcher_' + str(run) + '.root')
    T = root['BeamTree']
    TOR875 = T['E_TOR875'].array(library="np")
    TOR860 = T['E_TOR860'].array(library="np")

    for j in range(len(TOR875)):

        # only count POT if positive
        if TOR875[j] >= 0:
            pot_875 += TOR875[j]

        if TOR860[j] >= 0:
            pot_860 += TOR860[j]

    print('\n#########################################################\n')
    print(pot_875, 'e12 POT (E:TOR875)')
    print(pot_860, 'e12 POT (E:TOR860)')
    print('\n#########################################################\n')
    time.sleep(3)

    # TODO: append results to a root file or csv file

    return pot_875, pot_860