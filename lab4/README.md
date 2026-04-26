# Instructions to Run the simulations process the results

- To run the simulations use the script `studies.sh`. 
  - By running the script with the number of the study you will get instructions on how to use the 
  script for each particular study.
  - The vauilable options are:
    - `./studies.sh <study_nr>`, where `<study_nr>` might be: 
	- `1|one|first`  
	- `2|two|second` 
	- `3|three|third`
 	- `4|four|fourth` 

- The simulations might take a while but once the results are available they got tothe directory in
the path `/home/mobile/ns-3.47/scratch`. From here I opted for creating a directory in this same path
for each of the studies [`1st-study-res`, `1st-study-res-10dBm`, `2nd-study-res`,`3rd-study-res`,
`4th-study-res`]. This allowed me to store the results of each simulation (which are either `*.xml` 
or `*.pcap` files) separately for post'processing.

- With the results in these formats we have to use the `flowmon-wrapper.py` or  `process'pcap.py` 
script to parse the results to a text file and then the script `flowmon-2csv.py` to parse the text 
results into `*.csv`which is great for plots in `python`.

- Having the `*.csv` files we can use the script `study-plot.py` to generate the plots and store 
them in `*.png` format.


