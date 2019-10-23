# Import required library
import argparse
import os
import statistics
import json
import requests
import geopandas as gpd
import shutil

# Define parser argument for input and output files
def get_parser_argument():
    parser = argparse.ArgumentParser(description='Convert Point or LineString OSM Data to Polygon')
    parser.add_argument("input_bbox",type=str, help="Input BBOX for workspace (such as '48.5151, 9.0392, 48.5281, 9.0728' )")
    parser.add_argument("output", help="Input working area or project name (such as helsinki)", default='osm2rn_project')
    args = parser.parse_args()

    # Assign input_bbox to bbox variable
    bbox = args.input_bbox

    # Assign output file name to output variable
    working_area = args.output

    return bbox, working_area


# Create needed directories for each working area
def create_dir():
    _, working_area = get_parser_argument()
    file_path = os.path.join(data_dir,working_area)
    if not os.path.exists(file_path):
        os.makedirs(file_path,mode = 0o777, exist_ok = False)
        print('{} directory created.'. format(data_dir))
    else:
        print("Directory ", os.path.join(data_dir,working_area), " already exists.")


# Download OSM data with Overpass API
def get_json_data():
    # Check if exits BBOX OSM Data
    exists = os.path.isfile(os.path.join(data_dir,working_area,working_area+'.json'))
    if exists:
        print('.............................................')
        print('{} file elrady exists. \n Skipped download JSON data from Overpass API'.format(json_file_path))
        print('.............................................')
    else:
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = """
        [out:json];
        // gather results
        (
          // query part for: “highway=*”
          node["highway"]("""+bbox+""");
          way["highway"]("""+bbox+""");
          relation["highway"]("""+bbox+""");
        );
        // print results
        out body;
        >;
        out skel qt;
        """
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()
        with open(os.path.join(data_dir,working_area,working_area+'.json'), 'w') as fp:
         json.dump(data, fp)


# Convert downloaded OSM data in json to geojson
def convert_json_2_geojson():
    exist_json = os.path.isfile(os.path.join(data_dir, working_area, working_area+'.json'))
    exist_geojson = os.path.isfile(os.path.join(data_dir, working_area, working_area+'.geojson'))

    # If geojson file exist
    if exist_geojson:
        print('.............................................')
        print('{} file elrady exists. \n Skipped convert json to Geojson'.format(os.path.join(data_dir, working_area, working_area+'geojson')))
        print('.............................................')
    else:
        if exist_json:
            print('Found {} file to convert Geojson...\n Started conversion...\n Please wait'.format(os.path.join(data_dir,working_area,working_area+'.geojson')))
            # Convert json to geojson
            convert_command = 'osmtogeojson ' + os.path.join(data_dir,working_area,working_area+'.json') + '>' + os.path.join(data_dir,working_area,working_area+'.geojson')
            os.system(convert_command)
            print('Conversion json to geojson finished...')
            print('.............................................')


# read geojson file
def read_file():
    #chech_file(input)
    data = gpd.read_file(os.path.join(data_dir,working_area,working_area+'.geojson'))
    return data


# Check for lanes and and width:lanes columns in existing data file
# Add columns that don't exist.
def check_lane_width():
    data = read_file()
    mycols = ['lanes', 'width:lanes']
    new_write = 0
    for a_mycols in mycols:
        if {'lanes'}.issubset(data.columns):
            print('{} already exist'.format(a_mycols))
        else:
            print('{} not exist'.format(a_mycols))
            new_write = 1
            # Add a new column with None value
            data.assign(a_mycols=None)

    if new_write == 1:
        # Write Polygon data to input file
        print('Please wait. checked geojson file has beeen writing to disk...')
        data.to_file(os.path.join(data_dir, working_area, working_area+'_checked.geojson'), driver='GeoJSON')
        print('Successfully Finished!')
    else:
        shutil.copyfile(os.path.join(data_dir,working_area, working_area+'.geojson'), os.path.join(data_dir, working_area, working_area+'_checked.geojson'))
        print('Copyied successfull...')


# chech shoulder data exist or not
def shoulder_exist():
    data = read_file()
    if {'shoulder'}.issubset(data.columns):
        result = 'yes'
    else:
        result = 'no'
    return result


def convert_width_lanes(input_row):
    total_num = 0
    total_width = 0
    for num in input_row.split("|"):
        total_num = total_num + 1
        total_width = total_width + float(num)
    mean_width = total_width / total_num
    return mean_width

# Write created data to geojson file
def write_data(input_data):
    input_data.to_file(os.path.join(data_dir, working_area, 'final_'+working_area + '.geojson'), driver='GeoJSON')


# get shoulder rows that contain shoulder and width keys
def get_shoulder_cols_width():
    data = read_file()
    shoulder_cols_list = []
    empty_shoulder_cols_dict = {}

    # define string for find cols that contain shoulder width
    string1 = 'shoulder'
    string2 = 'width'
    cols_list = ['lanes', 'width:lanes']
    for col in data.columns:
        if (string1 in col) and (string2 in col):
            shoulder_cols_list.append(col)
    print('Founded shoulder cols that contain {}, {} strings : {} '.format(string1, string2, shoulder_cols_list))
    final_cols = list(set(cols_list + shoulder_cols_list))
    for a_road in roads:
        empty_shoulder_cols_dict[a_road] = a_road
        empty_shoulder_cols_dict[a_road] = dict(zip(final_cols, [[] for x in final_cols]))
    return final_cols, shoulder_cols_list, empty_shoulder_cols_dict


# Assign values to emtp dictionary
def assign_value_to_empty_dict():
    data = read_file()
    count_row = data.shape[0]
    print('Total row in read file: : ', count_row)

    for index, row in data.iterrows():
        road_type = row['highway']
        if road_type in roads:
            for a_col in called_final_cols:
                if row[a_col] is not None and row[a_col].isdigit() == True:
                    shoulder_cols_dict_empty[road_type][a_col].extend([row[a_col]])
    print('Created final empty dict: ', shoulder_cols_dict_empty)
    return shoulder_cols_dict_empty


# Calculate mean shoulder values
def calc_shoulder_cols_mean():
    data = read_file()
    for each in assigned_value_to_dict.keys():
        counter = 0
        if isinstance(assigned_value_to_dict[each], dict):
            for each_1 in assigned_value_to_dict[each].keys():
                # get list in nested dictionary
                get_list = assigned_value_to_dict.get(each).get(each_1)
                # if the list (get_list) has one or more items
                # calculate the mean of list items
                if len(get_list) > 0:
                    get_list = map(int, get_list)
                    mean_list = statistics.mean(get_list)
                    print('Mean of list : ', mean_list)
                    assigned_value_to_dict[each][each_1] = mean_list
                else:
                    assigned_value_to_dict[each][each_1] = 0
    print('Final dictionary with assigned value :  ', assigned_value_to_dict)
    return assigned_value_to_dict


# Convert linestring to polygon with calculated total road width
def convert_to_polygon():
    # read checked geojson file
    data = gpd.read_file(os.path.join(data_dir, working_area, working_area+'_checked.geojson'))
    for index, row in data.iterrows():
        geometry = row['geometry']
        if geometry.type =='Polygon':
            data = data.drop(index)
            print('Deleted index : ',index)
            print('Geometrytype : ', geometry.type)

    for index, row in data.iterrows():
        road_type=row['highway']
        if road_type in roads:
                # calc sum of lanes
            if (row['lanes'] == None):
                row['lanes'] = final_dict_with_mean_value[road_type]['lanes']
                print('{}. row[lanes] = {} '.format((index+1), row['lanes']))
            else:
                row['lanes'] = standart_values[road_type]['lanes']
                print('{}. row[lanes] = {} '.format((index+1), standart_values[road_type]['lanes']))

            # calc the sum of lanes widths
            if (row['width:lanes'] == None):
                row['width:lanes'] = final_dict_with_mean_value[road_type]['width:lanes']
                print('{}. row[width:lanes] = {} '.format((index+1), row['width:lanes']))
            else:
                row['width:lanes'] = standart_values[road_type]['width:lanes']
                print('{}. row[width:lanes] = {} '.format((index+1), standart_values[road_type]['width:lanes']))

            # get width cols and assign calculated values
            for a_col in called_final_cols:
                if row[a_col] == None:
                    row[a_col] = final_dict_with_mean_value[road_type][a_col]
                    print('{}. row[{}] = {} '.format((index + 1), a_col, final_dict_with_mean_value[road_type][a_col]))
            print(' ')

    # get current Coordinate Reference Systems (CRS)
    current_crs = data.crs['init']

    # Change CRSto EPSG 3395     # to calculate road with in meters
    data.to_crs(epsg=3395, inplace=True)

    # Write final data read file
    for index, row in data.iterrows():
        road_type=row['highway']

        # check road_type in roads list
        if road_type in roads:
            if row['width'] != None and  (isinstance(row['width'], (int, float))):
                data.loc[index, 'geometry'] = row['geometry'].buffer(row['width'])
                print('row["width"] : ', row['width'])
            else:
                lanes_1 = standart_values[road_type]['lanes']
                width_lanes_1 = standart_values[road_type]['width:lanes']

                # calc sum of lanes
                if (row['lanes'] != 0) and (isinstance(row['lanes'], (int, float))):
                    lanes_1 = row['lanes']
                if (row['width:lanes'] != 0) and (isinstance(row['width:lanes'], (int, float))):
                    width_lanes_1 = row['width:lanes']

                # get width cols and assign calculated values
                total_shoulder_1 = 0
                if len(called_shoulder_cols_list) > 0:
                    for a_col in called_shoulder_cols_list:
                        if (row[a_col] != 0) and (isinstance(row[a_col], (int, float))):
                            total_shoulder_1 = total_shoulder_1 + row[a_col]
                else:
                    total_shoulder_1 = standart_values[road_type]['shoulder_width']

                final_total_road_width = lanes_1 * width_lanes_1 + total_shoulder_1
                data.loc[index, 'geometry'] = row['geometry'].buffer(final_total_road_width)
                print('........................ {}. row ........................ '.format((index + 1)))
                print('{}. row[geometry] = {}'.format((index + 1), final_total_road_width))
                print('Calculated lane : ', lanes_1)
                print('Calculated width of lane : ', width_lanes_1)
                print('Calculated shoulder width : ', total_shoulder_1)
                print('Calculated total road width (FINAL) : ', final_total_road_width)
                print(' ')
        else:
            data.loc[index, 'geometry'] = row['geometry'].buffer(0)

    # Change CRS to old value
    print('CRS has changed to epsg=4326')
    data.to_crs(epsg=4326, inplace=True)

    # Write Polygon data to input file
    print('Please wait. Created geojson file has beeen writing to disk...')
    write_data(input_data = data)
    print('Successfully Finished! Your final result file is {}  '.format('final_' + working_area + '.geojson'))


if __name__ == "__main__":
    # Set standard values for the number of lanes, lane width and shoulder width parameters for each road type
    standart_values = {'motorway': {'lanes': 3, 'width:lanes': 3.6, 'shoulder_width': 1.8}, \
                       'trunk': {'lanes': 3, 'width:lanes': 3.6, 'shoulder_width': 1.2}, \
                       'primary': {'lanes': 2, 'width:lanes': 3.4, 'shoulder_width': 0.0}, \
                       'secondary': {'lanes': 2, 'width:lanes': 3.0, 'shoulder_width': 0.0}, \
                       'tertiary': {'lanes': 2, 'width:lanes': 2.8, 'shoulder_width': 0.0}, \
                       'unclassified': {'lanes': 1, 'width:lanes': 4.2, 'shoulder_width': 0.0}, \
                       'residential': {'lanes': 1, 'width:lanes': 4.2, 'shoulder_width': 0.0}, \
                       'service': {'lanes': 1, 'width:lanes': 3.8, 'shoulder_width': 0.0}, \
                       'primary_link': {'lanes': 1, 'width:lanes': 3.8, 'shoulder_width': 0.0}
                       }

    # the list that contains road type for vehicles
    roads = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'service',
             'primary_link']

    bbox, working_area = get_parser_argument()

    # Define fata folder for the working area
    data_dir = 'data'

    create_dir()

    get_json_data()
    convert_json_2_geojson()

    check_lane_width()

    called_final_cols, called_shoulder_cols_list, shoulder_cols_dict_empty = get_shoulder_cols_width()
    print('Called final cols list : ', called_final_cols)
    print('Called shoulder cols list : ', called_shoulder_cols_list)
    print('Called created empty dict : ', shoulder_cols_dict_empty)

    assigned_value_to_dict = assign_value_to_empty_dict()
    print('assigned_value_to_dict : ', assigned_value_to_dict)

    final_dict_with_mean_value = calc_shoulder_cols_mean()
    print('Created dict with mean value : ', final_dict_with_mean_value)

    convert_to_polygon()
