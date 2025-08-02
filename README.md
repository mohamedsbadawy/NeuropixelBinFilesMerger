# imec Binary Files Merger

## Overview
This Python class provides a Python-based tool for merging `.bin` files from IMEC Neuropixels recordings. The script identifies corresponding `.bin` and `.meta` files in different directories and combines them while preserving file structure and metadata integrity.

## Requirements
- Python 3.7+
- No additional dependencies (uses built-in libraries)

## Usage

### 1. Clone the Repository
```sh
git clone https://github.com/mohamedsbadawy/NeuropixelBinFilesMerger.git
cd NeuropixelBinFilesMerger
```

### 2. Run the Script
Modify the paths to your datasets and execute the script:
```sh
from NPMerger import NeuropixelsMerger
merger = NeuropixelsMerger(
        dir1=r'Z:\~\(imec_directory)\directory_1_g0',
        dir2=r'Z:\~\(imec_directory)\directory_2_g0',
        output_dir=r'ZZ:\~\(imec_directory)\directory_merged_g0',
        extension='lf.bin', # or ap.bin
        time_range1 = tuple (0,1000), #time in seconds to the part of probe(s) 1 to merge to probe 2- default none and merge the whole file.
        time_range2 = tuple( 0,100) #default none and merge the whole file.
    )
    merger.merge_matching_files()
    merger.fix_meta_files()

```

### 3. File Structure
Ensure your directory contains subfolders with `imecX` structure (e.g., `imec0`, `imec1`). Example:
```
📂 Project_Folder
 ├── 📂 imec0
 │    ├── file1.ap.bin
 │    ├── file1.ap.meta
 │    ├── file2.ap.bin
 │    ├── file2.ap.meta
 │
 ├── 📂 imec1
 │    ├── file1.ap.bin
 │    ├── file1.ap.meta
```
## Notes
- Ensure both directories contain the same number of `.ap.bin` and `.meta` files.
- The script automatically skips directories with missing or mismatched files.

## License
This project is licensed under the MIT License. Feel free to modify and distribute it.


