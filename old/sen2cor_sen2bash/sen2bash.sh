#!/bin/bash

# normal bash command to execute sen2cor
# Sen2Cor-02.08.00-Linux64/bin/L2A_Process /path/

printf "\n"
echo "==============================="
echo "=== | Sen2Core | 02.08.00 | ==="
echo "==============================="

printf "\n\nEnter path to your input directory (all Sentinel.SAFE files): \n"
read input_dir
#/path

printf "\n\nEnter path to your output directory (for L2A processed data): \n"
read output_dir
#/path

cd $input_dir

sub=".SAFE"
counter=1
# looping through directories
for d in *; do
    str=$input_dir/$d
        if [[ "$str" == *"$sub" ]]; 
        then bash $HOME/Sen2Cor-02.08.00-Linux64/bin/L2A_Process --output_dir $output_dir $input_dir/$d/ 
        printf "\n"
        echo "==============================="
        echo " ===== File $counter processed ===== "
        echo "==============================="
        ((counter++))
        fi
done

printf "\n\n"
echo "==============================="
echo "===== Processing finished ====="
echo "==============================="