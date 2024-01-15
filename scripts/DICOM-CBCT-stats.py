"""
DICOM Header Extraction to CSV

This script processes a directory containing DICOM files (including those without extensions),
extracts the header information from each file, and writes the headers to a CSV file. Each
unique DICOM examination, identified by the Series Instance UID Attribute (SeriesInstanceUID (0020,000E)), is stored in the CSV.
The script dynamically adds new columns to the CSV for any new DICOM fields encountered.

The script is specially adaptet to extract data from our two modalities Morita Accuitomo 170 and Planmeca Promax Mid and our local setup of the Sectra PACS.
You might need to adjust it for use on your setup.

Special adaptions:
- Morita Accuitomo 170 saves the DAP dose to the field ImageComment, the value is extracted from that field 
- Planmeca Promax does not store number of slices i.e. Images in Acquisition Attribute (ImagesInAcquisition (0020,1002)) so the files in the examination folder have to be counted to set this value.
- Planmeca Promax stores the dose in 1/100 of mGycm2, so the value is multiplied by 100 to be correct
- Stacks and images generated as copies (derived) in the Sectra PACS are not included (ImageType contains string "DERIVED")

Usage:
- Set 'directory_path' to the path of the directory containing DICOM files.
- Set 'output_csv' to the desired path for the output CSV file.
- Run the script.

Dependencies:
- pydicom: Install using `pip install pydicom`

Creator: Gerald Torgersen 
www.odont.uio.no/iko/english/people/aca/gerald
2024
License: CC BY 4.0 DEED https://creativecommons.org/licenses/by/4.0/ 
"""

import os
import re
import pydicom
import csv
from pydicom.errors import InvalidDicomError
from pydicom.tag import Tag

def is_dicom_file(filename):
    """Check if a file is a valid DICOM file."""
    try:
        with pydicom.dcmread(filename, stop_before_pixels=True):
            return True
    except InvalidDicomError:
        return False


def process_directory(directory_path):
    """
    Process the given directory to find DICOM files and extract their headers.
    
    Args:
    - directory_path: Path to the directory containing DICOM files.

    Returns:
    - A dictionary with Series Instance UIDs as keys and DICOM datasets as values.
    """
    dicom_headers = {}
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            if is_dicom_file(file_path):
                dicom = pydicom.dcmread(file_path, stop_before_pixels=True)
                if "DERIVED" in getattr(dicom, "ImageType", None):
                    continue # do not include derived examinations
                series_instance_uid = getattr(dicom, "SeriesInstanceUID", None)
                if series_instance_uid and series_instance_uid not in dicom_headers:
                    if "Morita" in getattr(dicom, 'Manufacturer', None).strip():
                        DAP_dose = extract_value_from_comments(getattr(dicom, "ImageComments", None), "DAP:(\d+mGycm2)") # handle storage of DAP DOSE
                        dicom.AcquiredImageAreaDoseProduct = float(DAP_dose)
                    elif "Planmeca" in getattr(dicom, 'Manufacturer', None).strip(): # handle number of slices in Promax
                        dicom.ImagesInAcquisition = int(count_files(root))
                        dicom.AcquiredImageAreaDoseProduct = float(dicom.AcquiredImageAreaDoseProduct)*100.0 # Adjust dose from Promax
                    # Store header data
                    dicom_headers[series_instance_uid] = dicom


    return dicom_headers

def clean_value(value):
    """
    Clean the DICOM field value by removing line feeds and other special characters.
    
    Args:
    - value: The original value of the DICOM field.

    Returns:
    - A cleaned string value suitable for CSV.
    """
    if isinstance(value, str):
        return value.replace('\n', ' ').replace('\r', ' ').replace(',', ';')
    return value

def extract_value_from_comments(comments, pattern):
    """
    Extracts a specific value from the comments string based on the given pattern.

    Args:
    - comments: The comments string from which to extract the value.
    - pattern: The regex pattern to identify the specific part of the comments.

    Returns:
    - The extracted value or None if not found.
    """
    match = re.search(pattern, comments)
    match = re.search(r"[-+]?\d*\.\d+|\d+", match.group(0)) # Get just the number
    if match:
        return match.group(0)
    return None

def count_files(file_path):
    """
    Counts the number of files in directory to set number of slices

    Args:
    Path to directory

    Returns:
    Number of files
    """

    if not os.path.exists(file_path):
        return 0

    file_count = 0
    for root, _, files in os.walk(file_path):
        for file in files:
            if os.path.isfile(os.path.join(root, file)):
                file_count += 1
    
    return file_count

def dicom_headers_to_csv(dicom_headers, output_csv, select):
    """
    Write the DICOM headers to a CSV file, ensuring special characters are handled.

    Args:
    - dicom_headers: A dictionary of DICOM datasets.
    - output_csv: Path to the output CSV file.
    """
    fieldnames = select
    # fieldnames = set()
    # for dicom in dicom_headers.values():
    #     fieldnames.update(dicom.dir())
    # fieldnames = sorted(fieldnames)

    with open(output_csv, mode='w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for dicom in dicom_headers.values():
            row = {field: clean_value(getattr(dicom, field, "")) for field in fieldnames}
            #selected_row = {col: row[col] for col in select if col in row}
            writer.writerow(row)

# Directory containing DICOM files
directory_path = 'your path to DICOM root directory'
output_csv_path = 'your path to and filename of csv file'

selected_columns = [
    "AccessionNumber", "SeriesInstanceUID", "StudyDate", "StudyTime",
    "PatientBirthDate", "PatientSex",
    "KVP", "XRayTubeCurrent", "ExposureTime", "AcquiredImageAreaDoseProduct",
    "Columns", "Rows", "PixelSpacing", "ImagesInAcquisition", "SliceThickness", 
    "Manufacturer", "StationName", "ManufacturerModelName",
    "ImageComments"
]  # Replace with your column names of choice

# Process the directory and write to CSV
dicom_headers = process_directory(directory_path)
dicom_headers_to_csv(dicom_headers, output_csv_path, selected_columns)
