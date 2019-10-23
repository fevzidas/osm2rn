# OSM2RN

OSM2RN is an acronym for "OpenStreetMap to Road Network". OSM2RN is an open source tool for extraction of road network from OpenStreetMap. This tool is coded with Python. This tool performs the following steps to extract the road network from the OSM data:

- The project name and BBOX values are entered by the user with the execution of the program.
- It downloads the data of the area defined by the user with BBOX in json format.
- OSM data in JSON is converted to GEOJSON with osmtogeojson tool.
- Missing data is completed.
- Width calculations are made for all roads in downloaded OSM data.
- By applying a buffer to the calculated road widths, linestring objects are converted to polygon objects.
- The resulting new data is written to a new geojson file.
- How to works OSM2RN (Tutorial Video on Youtube) https://youtu.be/WTSNJMb9jXo
