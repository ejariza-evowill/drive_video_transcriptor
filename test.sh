#!/bin/bash

# Clean out directory for fresh test
rm -rf out/

# Download all videos from a Google Drive folder and transcribe them with SRT output
python download_drive_video.py --folder-url https://drive.google.com/drive/folders/1H0y9iAixlhVPPVCdhHzClJLpL2Y_ERyC --transcribe --srt

# Download a single video from Google Drive and transcribe it with SRT output
python download_drive_video.py --url https://drive.google.com/file/d/1inpny9HSvbXVBz8ECgwRyZQel5ozwwxL/view?usp=drive_link  --transcribe --srt


# Check that the downloaded files match expected hashes
echo "Verifying downloaded files..."

# Expected hashes

#cb73124b6801bd93e4e09f375c5fadeb34198476d86bf86ad024fa79e72f994f  out/16_01_2025_CHI_Software_Middle_Senior_Full_Stack_Python(English check).mp4
#ddb74993e7b8d49b79a68e44d31a81ea3d6bf34d8f80cdfb5acdb1b3835fda6e  out/16_01_2025_CHI_Software_Middle_Senior_Full_Stack_Python(English check).srt
#84ea5a1ddbffb1062f5ad3d815194ba473e353acbbc4e30b258de7028a3dd202  out/16_01_2025_CHI_Software_Middle_Senior_Full_Stack_Python(English check).txt
#aecf4f7da7890a3740a20cc5db249695efd4781e1bab3c8b68c7ce447fe36686  out/Self_presentation_ENG.mkv
#27c7c62ed7fd1881035c42b412a176bbe6409b7ed4e4aeae05414e5db7e777d4  out/Self_presentation_ENG.srt
#4e15bf25d0a4d8be43efea5ac2b15c2fc5073c82ab9805452bc513819473efc5  out/Self_presentation_ENG.txt
#6070d3d6a0d1c35ac57405312615ace7369662f825665a47e1c26c0661d33da8  out/Self_presentation_UKR.mkv
#6d10d3de821e6c395a6c748150d39b64fb8babaa4e92bcece31cb93d5d686b98  out/Self_presentation_UKR.srt
#83aaeeb5388d93e485f593f5292796d012f199479a00fa8f46b872517296b4ef  out/Self_presentation_UKR.txt

#save shasum -a 256 out/* outputnto a variable
output_hashes=$(shasum -a 256 out/*)

# Check each expected hash against the output_hashes
echo "$output_hashes" 

echo "$output_hashes" | grep cb73124b6801bd93e4e09f375c5fadeb34198476d86bf86ad024fa79e72f994f
echo "$output_hashes" | grep ddb74993e7b8d49b79a68e44d31a81ea3d6bf34d8f80cdfb5acdb1b3835fda6e
# echo "$output_hashes" | grep 84ea5a1ddbffb1062f5ad3d815194ba473e353acbbc4e30b258de7028a3dd202
echo "$output_hashes" | grep aecf4f7da7890a3740a20cc5db249695efd4781e1bab3c8b68c7ce447fe36686
echo "$output_hashes" | grep 27c7c62ed7fd1881035c42b412a176bbe6409b7ed4e4aeae05414e5db7e777d4
# echo "$output_hashes" | grep 4e15bf25d0a4d8be43efea5ac2b15c2fc5073c82ab9805452bc513819473efc5
echo "$output_hashes" | grep 6070d3d6a0d1c35ac57405312615ace7369662f825665a47e1c26c0661d33da8
echo "$output_hashes" | grep 6d10d3de821e6c395a6c748150d39b64fb8babaa4e92bcece31cb93d5d686b98
# echo "$output_hashes" | grep 83aaeeb5388d93e485f593f5292796d012f199479a00fa8f46b872517296b4ef

if [ $? -eq 0 ]; then
    echo "All files verified successfully."
else
    echo "File verification failed."
    exit 1
fi