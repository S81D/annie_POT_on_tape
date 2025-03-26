#############################################################
# ******* Calculate POT recorded on tape for ANNIE ******** #
#                                                           #
# Script will run the BeamFetcherV2 toolchain to fetch beam #
# database timestamps and beam information, pairing them    #
# with our recorded CTC timestamp. It will write this info  #
# to a beamfetcher root file to be stored in persistent/    #
# and to be used for the event building process.            #
#                                                           #
# The script will also calculate the total POT from those   #
# root files for both the downstream and upstream toroid,   #
# and display them for the user.                            #
#                                                           #
# Author: Steven Doran                                      #
#############################################################

import os
import time
from lib import help as help
import subprocess
import re

#
#
#

'''@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'''

''' Please modify the following to reflect your working directory '''

user = '<user>'                   # anniegpvm username

# bind mounted path for entering your container
singularity = '-B/pnfs:/pnfs,/exp/annie/app/users/' + user + '/temp_directory:/tmp,/exp/annie/data:/exp/annie/data,/exp/annie/app:/exp/annie/app'

TA_folder = '<my_toolanalysis/'   # name of the ToolAnalysis folder to run the BeamFetcherV2 toolchain

BF_step_size = 10                 # number of part files per step to execute the BeamFetcher toolchain (default = 10)

SQL_file = 'ANNIE_SQL_RUNS.txt'   # SQL filename

'''@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'''

#
#
#
#
#
#

# constructed paths based on user customization and current areas of data

app_path = '/exp/annie/app/users/' + user + '/' + TA_folder + '/'                                  # TA folder used for running the BeamFetcherV2 toolchain

pwd_path = os.getcwd()                                                                             # present working directory

beamfetcher_path = '/pnfs/annie/persistent/processed/BeamFetcherV2/'                               # BeamFetcherV2 root files

raw_path = '/pnfs/annie/persistent/raw/raw/'                                                       # raw data location, transferred from the DAQ


print('\n\n**********************************************************\n')
user_confirm = input('The current user is set to ' + user + ', is this correct? (y/n):      ')
if user_confirm == 'n':
    user = input('\nPlease enter the correct user name:      ')
    print('\nUser has been set to ' + user + ', locking in changes...')
    time.sleep(3)
elif user_confirm != 'y' and user_confirm != 'n':
    print('\nInvalid response - please restart script\n')
    exit()
print('\n')

# obtain run range from the user
runs_to_run_user = help.get_runs_from_user()

# filter runs provided by the user to only run over beam type and grab their start + end times
start_time, end_time, beam_runs_to_run = help.read_SQL(SQL_file, runs_to_run_user)
print('\n')

# we have to make sure there are RAWData for each run [rpvoded]
print('\nVetting the runs you submitted...')
runs_to_run = help.is_there_raw(beam_runs_to_run, raw_path)

print('\n')
print('  - BeamFetcherV2 ToolAnalysis path: ', app_path)
print('  - Runs to run: ', runs_to_run)
print('  - Start time: ', start_time)
print('  - End time: ', end_time)
print('\n')
time.sleep(1)
print('Locking arguments in...')
for i in range(5):
    print(str(5-i) + '...')
    time.sleep(1)
print('\n\nProceeding with script...')
time.sleep(1)

# execute the toolchain and calculate the total recorded POT
total_pot_875 = 0; total_pot_860 = 0
for run in runs_to_run:
    help.beamfetcher(run, BF_step_size, raw_path, app_path, pwd_path, singularity, beamfetcher_path)
    pot_875, pot_860 = help.POT(run, beamfetcher_path)
    total_pot_875 += pot_875; total_pot_860 += pot_860


# fetch the delivered POT from the booster
print('\nQuerying the beam database for the delivered POT... (this may take a minute)')
print('Start time:', start_time, ', End time:', end_time)
#os.system('python3 querybnb_ind.py "' + start_time + '" "' + end_time + '"')
delivered_pot = help.python_query(start_time, end_time)    # query the database using Marvin's tool

print('\n\n')
print('For runs: ', runs_to_run, '\n')
print('Total POT (e12)')
print('---------------------')
print(total_pot_860, ' [TOR860]')
print(total_pot_875, ' [TOR875]')
print('\n')

print('Delivered POT from the BNB:', delivered_pot, 'e12\n')

eff = round(100*total_pot_875 / delivered_pot, 1)   # take it out of E:TOR875 for now
print('POT efficiency for ANNIE:', eff, '%')
print('\n')

# clean up
os.system('rm -rf beam.list')

# done
