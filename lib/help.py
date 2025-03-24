# helper functions

import uproot
import numpy as np
import os
import time
from datetime import datetime
import subprocess
import re


# ask user for runs you would like to include
def get_runs_from_user():

    runs = []
    try:
        first_run = int(input("Enter the earliest (first) run number: "))
        last_run = int(input("Enter the latest (last) run number: "))
        
        if first_run > last_run:
            print("\nError: The first run number must be less than or equal to the last run number! Exiting...\n")
            exit()
        
        return [str(run) for run in range(first_run, last_run + 1)]
    except ValueError:
        print("\nError: Invalid input. Please enter numeric run numbers! Exiting...\n")
        exit()


# check if there isn't RawData for any of the runs and omit that run from the list
def is_there_raw(runs_to_run_user, raw_path):
    temp_runs = []
    for i in range(len(runs_to_run_user)):
        if os.path.isdir(raw_path + runs_to_run_user[i] + '/'):
            temp_runs.append(runs_to_run_user[i])
        else:
            print('Run ' + runs_to_run_user[i] + ' does not have any RAWData!!! Removing from the list')
    return temp_runs


# grab SQL information for selected runs and their times / dates for the query tool
def read_SQL(SQL_file, runs):
    
    beam_run_types = {3, 34, 39}  # beam run types
    beam_runs = []
    
    if not os.path.isfile(SQL_file):
        print(f"\nERROR: The SQL file '{SQL_file}' does not exist. Please generate an SQL txt file.\nExiting...\n")
        exit()
    
    with open(SQL_file, 'r') as file:
        lines = file.readlines()[2:]
        for line in lines:
            columns = [col.strip() for col in line.split('|')]
            if len(columns) > 1:
                runnum = columns[1]
                runconfig = columns[5]   # Run type
                start = columns[3]       # UTC start time
                stop = columns[4]        # UTC stop time

                if runnum in runs and runconfig.isdigit() and int(runconfig) in beam_run_types:

                    # runs after 3869 have microsecond precision in their timestamps
                    try:
                        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
                    # for earlier runs, they are recorded to the nearest second
                    except ValueError:
                        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                    
                    if stop:
                        try:
                            stop_dt = datetime.strptime(stop, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            stop_dt = datetime.strptime(stop, "%Y-%m-%d %H:%M:%S")
                    else:
                        print(f"ERROR: Run {runnum} has no end time in the SQL file. Omitting this run from consideration.")
                        continue
                    
                    beam_runs.append((runnum, start_dt, stop_dt))
    
    if not beam_runs:
        print("\nERROR: No valid beam runs found. Exiting...\n")
        exit()
    
    beam_runs.sort(key=lambda x: x[1])  # sort by start time
    earliest_start = beam_runs[0][1]
    
    # find the latest stop time
    # sometimes there are runs without an end time - omit those runs (second latest run will be the end of the range)
    latest_stop = None
    for run in reversed(beam_runs):
        if run[2]:
            latest_stop = run[2]
            break
    
    if not latest_stop:
        print("\nERROR: No valid end times found for beam runs. Exiting...\n")
        exit()
    
    print(f"Earliest beam run start time: {earliest_start}")
    print(f"Latest beam run end time: {latest_stop}")

    # only return a list of runs for beam_runs
    beam_run_numbers = [run[0] for run in beam_runs]
    beam_run_numbers.sort()
    
    return earliest_start, latest_stop, beam_runs


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


# Marvin's python query tool to obtain delivered POT
def python_query(start_time, end_time):

    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")

    cmd = ['python3', 'querybnb_ind.py', start_time_str, end_time_str]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        
        match = re.search(r"BNB: Total POT collected in the time interval selected: ([\d\.]+)", output)
        if match:
            total_pot = float(match.group(1))
            return total_pot
        else:
            print("Failed to extract POT value from output.")
            return None  

    except subprocess.CalledProcessError as e:
        print(f"Error running the query script: {e}")
        return None