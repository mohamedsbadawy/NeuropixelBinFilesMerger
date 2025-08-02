import os
import glob
import re
from pathlib import Path
from typing import Dict, List, Generator

class NeuropixelsMerger:
    '''
    This project provides a Python-based tool for merging `.bin` files from IMEC Neuropixels recordings. It ensures efficient handling of large binary files and maintains accurate metadata updates during the merging process. 
    The script identifies corresponding `.bin` and `.meta` files in different directories and combines them while preserving file structure and metadata integrity.
    Author: https://github.com/mohamedsbadawy
    '''
    def __init__(self, dir1: str, dir2: str, output_dir: str, extension: str,time_range1:tuple=None,time_range2:tuple=None):
        self.dir1 = dir1
        self.dir2 = dir2
        self.output_dir = output_dir
        self.extension = extension
        self.time_range1 = time_range1
        self.time_range2 = time_range2
        self.totalSize = None
        os.makedirs(output_dir, exist_ok=True)
    
    def read_file_chunks(self, file_path: str, chunk_size: int = 128 * 1024 * 1024) -> Generator[bytes, None, None]:
        """Generator to read a file in chunks."""
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
            raise
    
    def merge_ap_bin(
        self,
        file1: str,
        file2: str,
        output_file: str,
        file1_time_range: tuple[float, float] = None,
        file2_time_range: tuple[float, float] = None,
        meta1_path: str = None,
        meta2_path: str = None
    ) -> None:
        """
        Merges two .ap.bin files, optionally including only selected time ranges.

        Args:
            file1, file2 (str): Paths to the .ap.bin files.
            output_file (str): Path to the output file.
            file1_time_range, file2_time_range (tuple[float, float], optional): 
                Time ranges in seconds for each file.
            meta1_path, meta2_path (str, optional): Paths to .meta files (needed for sampling rate).
        """
        def get_byte_range(meta_path, time_range):
            with open(meta_path, 'r') as f:
                lines = f.readlines()
            meta = {line.split('=')[0]: line.split('=')[1].strip() for line in lines}
            fs = float(meta['imSampRate'])
            n_ch = int(meta['nSavedChans'])

            start_sample = int(time_range[0] * fs)
            end_sample = int(time_range[1] * fs)
            start_byte = start_sample * n_ch * 2
            end_byte = end_sample * n_ch * 2
            return start_byte, end_byte

        try:
            # Compute byte ranges from time ranges
            size1 = os.path.getsize(file1)
            size2 = os.path.getsize(file2)

            f1_start, f1_end = (0, size1)
            f2_start, f2_end = (0, size2)

            if file1_time_range and meta1_path:
                print(meta1_path)
                f1_start, f1_end = get_byte_range(meta1_path, file1_time_range)
            if file2_time_range and meta2_path:
                f2_start, f2_end = get_byte_range(meta2_path, file2_time_range)

            total_size = (f1_end - f1_start) + (f2_end - f2_start)
            bytes_written = 0

            print(f"Merging:")
            print(f"  {file1} bytes {f1_start} to {f1_end}")
            print(f"  {file2} bytes {f2_start} to {f2_end}")
            print(f"Output: {output_file}")

            with open(output_file, 'wb') as outfile:
                for path, start, end in [(file1, f1_start, f1_end), (file2, f2_start, f2_end)]:
                    with open(path, 'rb') as f:
                        f.seek(start)
                        to_read = end - start
                        while to_read > 0:
                            chunk = f.read(min(1024 * 1024, to_read))
                            if not chunk:
                                break
                            outfile.write(chunk)
                            to_read -= len(chunk)
                            bytes_written += len(chunk)
                            print(f"Progress: {bytes_written / total_size * 100:.2f}%", end='\r')

            print("\nMerging complete.")
            return total_size
        except Exception as e:
            print(f"Error merging files: {e}")
            if os.path.exists(output_file):
                os.remove(output_file)
            raise

    def get_ap_bin_files(self, directory: str, ext=None) -> Dict[str, List[str]]:
        if ext is None:
            ext = self.extension
        """Finds .ap.bin files in subdirectories."""
        ap_bin_files = {}
        for imec_folder in ["imec0", "imec1", "imec2", "imec3"]:
            matching_folders = glob.glob(str(Path(directory) / f"*{imec_folder}*"))
            for folder in matching_folders:
                if os.path.isdir(folder):
                    bin_files = sorted(glob.glob(os.path.join(folder, f"*.{ext}")))
                    if bin_files:
                        ap_bin_files[folder] = bin_files
        return ap_bin_files

    def extract_imec_number(self, folder_name: str) -> str:
        """Extracts the imec number from a folder name."""
        match = re.search(r'imec(\d+)', folder_name)
        return match.group(1) if match else None

    def merge_matching_files(self):
        """Matches and merges corresponding .ap.bin files."""
        files1, files2 = self.get_ap_bin_files(self.dir1), self.get_ap_bin_files(self.dir2)

        imec_map1 = {self.extract_imec_number(k): k for k in files1}
        imec_map2 = {self.extract_imec_number(k): k for k in files2}
        
        for imec_num in set(imec_map1.keys()) & set(imec_map2.keys()):
            for file1, file2 in zip(files1[imec_map1[imec_num]], files2[imec_map2[imec_num]]):
                output_folder = Path(self.output_dir) / Path(file2).parent.relative_to(self.dir2)
                output_folder.mkdir(parents=True, exist_ok=True)
                total_size = self.merge_ap_bin(file1, file2, str(output_folder / Path(file2).name),
                                               file1_time_range=self.time_range1,file2_time_range=self.time_range2,meta1_path=file1.replace(".bin",".meta"),meta2_path=file2.replace(".bin",".meta"))
        self.totalSize = total_size

    def read_meta(self, meta_path: str) -> Dict[str, str]:
        """Reads an ap.meta file into a dictionary."""
        meta_data = {}
        with open(meta_path, "r") as file:
            for line in file:
                key, value = line.strip().split("=")
                meta_data[key] = value
        return meta_data

    def merge_meta(self, meta1: Dict[str, str], meta2: Dict[str, str]) -> Dict[str, str]:
        """Merges two ap.meta dictionaries."""
        fs = float(meta1['imSampRate'])
        n_ch = int(meta1['nSavedChans'])
        if self.totalSize is not None:
            return {
            "fileSizeBytes": self.totalSize,
            "fileTimeSecs": self.totalSize / (2 * n_ch * fs),
            "firstSample": str(min(int(meta1["firstSample"]), int(meta2["firstSample"])))
        }
        else:
            return {
                "fileSizeBytes": str(int(meta1["fileSizeBytes"]) + int(meta2["fileSizeBytes"])),
                "fileTimeSecs": str(float(meta1["fileTimeSecs"]) + float(meta2["fileTimeSecs"])),
                "firstSample": str(min(int(meta1["firstSample"]), int(meta2["firstSample"])))
            }

    def write_meta(self, meta_path: str, meta_data: Dict[str, str]):
        """Writes a dictionary to an ap.meta file."""
        with open(meta_path, "w") as file:
            for key, value in meta_data.items():
                file.write(f"{key}={value}\n")

    def fix_meta_files(self):
        """Fixes and merges corresponding .meta files."""
        ext = self.extension.replace(".bin", ".meta")
        files1, files2 = self.get_ap_bin_files(self.dir1,ext), self.get_ap_bin_files(self.dir2,ext)
        imec_map1 = {self.extract_imec_number(k): k for k in files1}
        imec_map2 = {self.extract_imec_number(k): k for k in files2}
        
        for imec_num in set(imec_map1.keys()) & set(imec_map2.keys()):
            for file1, file2 in zip(files1[imec_map1[imec_num]], files2[imec_map2[imec_num]]):
                meta1, meta2 = self.read_meta(file1), self.read_meta(file2)
                merged_meta = self.merge_meta(meta1, meta2)
                output_folder = Path(self.output_dir) / Path(file2).parent.relative_to(self.dir2)
                output_folder.mkdir(parents=True, exist_ok=True)
                self.write_meta(str(output_folder / Path(file2).name), merged_meta)


