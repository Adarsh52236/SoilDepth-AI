IMPORTANT INFORMATION
If you use the ISMN data, please ensure that you correctly cite and acknowledge the ISMN and the contributing networks.
Check ismn_reference.bibtex for a list of ISMN and contributing network publications and ismn_acknowledgement.txt for
acknowledgement notes for contributing networks without publications.

Variables stored in separate files (Header+values)

Filename

	Data_separate_files_header_startdate(YYYYMMDD)_enddate(YYYYMMDD)_userid_randomstring_currrentdate(YYYYMMDD).zip
	
	e.g., Data_separate_files_header_20050316_20050601.zip

	
Folder structure

	Networkname
		Stationname

		
Dataset Filename

	CSE_Network_Station_Variablename_depthfrom_depthto_sensorname_redundancy_replacement_startdate_enddate.ext

	CSE	- Continental Scale Experiment (CSE) acronym, if not applicable use Networkname
	Network	- Network abbreviation (e.g., OZNET)
	Station	- Station name (e.g., Widgiewa)
	Variablename - Name of the variable in the file (e.g., Soil-Moisture)
	depthfrom - Depth in the ground in which the variable was observed (upper boundary)
	depthto	- Depth in the ground in which the variable was observed (lower boundary)
	Sensor name	- Name of the sensor used
    Redundancy Number - Indicates when multiple sensors are installed at the same depth and location
    Replacement Number - Indicates when a sensor has been exchanged at the very same position, e.g. due to malfunction
	startdate -	Date of the first dataset in the file (format YYYYMMDD)
	enddate	- Date of the last dataset in the file (format YYYYMMDD)
	ext	- Extension .stm (Soil Temperature and Soil Moisture Data Set see CEOP standard)
	
	e.g., OZNET_OZNET_Widgiewa_Soil-Temperature_0.150000_0.150000_CS616_1_2_20010103_20090812.stm

	
File Content Sample
	
	REMEDHUS   REMEDHUS        Zamarron          41.24100    -5.54300  855.00    0.05    0.05  (Header)
	2005/03/16 00:00    10.30 U	M	(Records)
	2005/03/16 01:00     9.80 U M

	
Header

	CSE Identifier - Continental Scale Experiment (CSE) acronym, if not applicable use Networkname
	Network	- Network abbreviation (e.g., OZNET)
	Station	- Station name (e.g., Widgiewa)
	Latitude - Decimal degrees. South is negative.
	Longitude - Decimal degrees. West is negative.
	Elevation - Meters above sea level
	Depth from - Depth in the ground in which the variable was observed (upper boundary)
	Depth to - Depth in the ground in which the variable was observed (lower boundary)

	
Record

	UTC Actual Date and Time
	yyyy/mm/dd HH:MM
	Variable Value
	ISMN Quality Flag
	Data Provider Quality Flag, if existing


Network Information

	SCAN
		Abstract: Soil Climate Analysis Network contains 239 stations all over the USA including stations in Alaska, Hawaii, Puerto Rico or even one in Antarctica. Apart from soil moisture and soil temperature, also precipitation and air temperature are measured. Some stations have also additional measurements of snow depth and snow water equivalent. Almost 150 stations are updated on daily basis. The network is operated by the USDA NRCS National Water and Climate Center with assistance from the USDA NRCS National Soil Survey Center.
		Continent: Americas
		Country: USA
		Stations: 222
		Status: running
Data Range: 

		Type: project
		Url: http://www.wcc.nrcs.usda.gov/
		Variables: air temperature, precipitation, snow depth, snow water equivalent, soil moisture, soil temperature, 
		Soil Moisture Depths: 0.05 - 0.05 m, 0.10 - 0.10 m, 0.15 - 0.15 m, 0.20 - 0.20 m, 0.25 - 0.25 m, 0.30 - 0.30 m, 0.38 - 0.38 m, 0.51 - 0.51 m, 0.61 - 0.61 m, 0.69 - 0.69 m, 0.76 - 0.76 m, 0.84 - 0.84 m, 0.89 - 0.89 m, 1.02 - 1.02 m, 1.09 - 1.09 m, 1.30 - 1.30 m, 1.42 - 1.42 m
		Soil Moisture Sensors: not-specified, Stevens-Hydraprobe-Analog, Stevens-Hydraprobe-Digital, 

