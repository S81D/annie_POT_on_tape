#!/bin/bash

BIND=$1
FILE_PATH=$2
RUN=$3
WHICH=$4

# copied from event building - only included the BeamFetcherV2 feature
if [ "$WHICH" == "beamfetcher" ]; then
    FILE_NAME="beamfetcher"
    TREE_NAME="BeamTree"
fi

singularity shell ${BIND} /cvmfs/singularity.opensciencegrid.org/anniesoft/toolanalysis\:latest/ << EOF

    root -l -q 'lib/mergeBeamTrees.C("$FILE_PATH", $RUN, "$FILE_NAME", "$TREE_NAME")'

    .q

    exit

EOF