# annie_POT_on_tape

Calculate recorded POT on tape in ANNIE and from the IFBeam Database. 

* ```main.py``` will execute the ```BeamFetcherV2``` toolchain in ToolAnalysis to query the database and grab timestamps + beam information that are within some time tolerance of our CTC timestamps. This "recorded" POT we have on tape is stored in a root file and saved in ```persistent/```, to be later used in the event building process. The script will also sum the POT from both toroid devices stored in the ```BeamFetcherV2``` root files for ANNIE (for the runs selected by the user) and print the total. 

* ```querybnb_ind.py``` fetches device information as recorded by the IFBeam database. Run this script within the ANNIE singularity container.

* `lib/` folder contains helper scripts.

Please only provide beam runs to the script.

### usage:
```python3 querybnb_ind.py "2024-03-27 11:24:55.511343" "2024-03-31 15:57:41.028200"```

```python3 main.py```

### Additional information
* Make sure to have a built, up-to-date copy of ToolAnalysis in your ```/exp/annie/app/<user>``` (this will be used to execute the ```BeamFetcherV2``` toolchain). Modify ```main.py``` to reflect your username and name of your Toolanalysis directory.
* In the process of running the toolchain, the scripts will enter the singularity container. Ensure the bind mounted folders in ```main.py``` within the singularity command are correct for you.
* There are two options to submit runs: manaully (enter run by run) or through a list. For running multiple runs (for a week's worth of data), it is easier to populate a list named ```runs.list``` with the associated run numbers. If you elect to use the list, make sure there is a ```runs.list``` present in the working directory.
