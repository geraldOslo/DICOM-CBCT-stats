# DICOM-CBCT-stats
Scripts to exctract relevant data from a structure of DICOM examinations for making statistics

The script extracts values from several DICOM fields to be used for statistics about use of CBCT. The script is specially adjusted for the setup and modalities used at our department and has to be adjusted for use at other institutions.

DICOM files have to be provideded in subdirectories of the working directory

Fields extracted:
    "AccessionNumber", "SeriesInstanceUID", "StudyDate", "StudyTime",
    "PatientBirthDate", "PatientSex",
    "KVP", "XRayTubeCurrent", "ExposureTime", "AcquiredImageAreaDoseProduct",
    "Columns", "Rows", "PixelSpacing", "SeriesDescription", "ImagesInAcquisition", "SliceThickness", 
    "Manufacturer", "StationName", "ManufacturerModelName",
    "ImageComments"

This can be changed by editing the variable selected_columns

Data are written to a csv-file
