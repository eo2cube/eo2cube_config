import yaml, uuid, glob, datetime, os
from osgeo import gdal, osr, ogr

#==============================================
#--- functions --------------------------------
#==============================================

# processing time (S2 template)
def format_time():
    t = datetime.datetime.now()
    s = t.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return s[:-3]+'Z'

# MODIS timestamp - day of the year
def format_time_MODIS(doy):
    year = int(doy[16:-18])
    days = int(doy[20:-15])
    t = datetime.datetime.now()
    s = datetime.datetime(year, 1, 1) + datetime.timedelta(days - 1)
    s = s.strftime('%Y-%m-%dT') + t.strftime('%H:%M:%S.%f')
    return s[:-3]+'Z'

# S1 timestamp - day of the year
def format_time_indices(doy):
    year = int(doy[24:-4])
    month = int(doy[18:-3])
    day = int(doy[21:])
    s = datetime.datetime(year, month, day)
    s = s.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return s[:-3]+'Z'

def format_time_sentinel1(doy):
    year = int(doy[0:4])
    month = int(doy[4:6])
    day = int(doy[6:8])
    s = datetime.datetime(year, month, day)
    s = s.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return s[:-3]+'Z'

# calculate right geo_ref_point, combine all corners
def geo_ref_points(path):
    ulx, xres, xskew, uly, yskew, yres  = path.GetGeoTransform()
    lrx = ulx + (raster.RasterXSize * xres)
    lry = uly + (raster.RasterYSize * yres)

    lrx = round(lrx,3)
    lry = round(lry,3)
    ulx = round(ulx,3)
    uly = round(uly,3)

    return (lrx, lry, ulx, uly)

# check for slash
def check_string(str):
    if str[-1] == "/":
        str = str
        return str
    else:
        str = str + "/"
        return str

#==============================================
#--- load up variables ------------------------
#==============================================

# choose a list of subproducts [un/comment]
index_list = 'VH','VV'
#index_list = 'ALP', 'ANI', 'ENT'

# choose orbit [un/comment]
#orbit = '_A_'
orbit = '_D_'

if index_list[0] == 'VH':
    product = 'COH'
else: 
    product = 'INT'

# output directory » *.yaml
output = '/media/SSD_Linux_Files/python_evns/metaIndexing/sentinel_1/data/yaml'
output = check_string(output)

# input directory » *.tiff
source_dir = '/media/SSD_Linux_Files/python_evns/metaIndexing/sentinel_1/data/' + product
source_dir = check_string(source_dir)

# extracting basenames from source_dir
source_list = [None] * len(index_list)

for i in range(len(index_list)):
    source_list[i] = glob.glob(source_dir + index_list[i] + '/*.tif', recursive=True)
    source_list[i].sort()
    source_list[i] = [x for x in source_list[i] if orbit in x]

if index_list[0] == 'VH':
    basename = []
    for i in source_list[0]:
        basename.append(os.path.basename(i)[:-4])
else:
    basename = []
    for i in source_list[0]:
        basename.append(os.path.basename(i)[:32])

#==============================================
#--- main loop | load up variables for yaml ---
#==============================================

if index_list[0] == 'VH':

    for i in range(len(source_list[0])):
        # open raster-file
        raster = gdal.Open(source_list[0][i])

        # load up geo_ref_points » in yaml: x and y
        coords = geo_ref_points(raster) 
        lrx = coords[0]
        lry = coords[1]
        ulx = coords[2]
        uly = coords[3]

        # load up geo_coordinates » in yaml: lat and lon
        info = gdal.Info(raster, format='json')
        geo = list(info['wgs84Extent']['coordinates'])
        llLat = geo[0][1][0]
        llLon = geo[0][1][1]
        lrLat = geo[0][2][0]
        lrLon = geo[0][2][1]
        ulLat = geo[0][0][0]
        ulLon = geo[0][0][1]
        urLat = geo[0][3][0]
        urLon = geo[0][3][1]

        timestring = basename[i].split('_')

        # additional product parameters
        product_type = 'SAR_COH'
        code = 'SENTINEL_1'
        instrument = 'SAR'
        timestamp = format_time_sentinel1(timestring[7])
        PROJCRS = raster.GetProjection()
        id = str(uuid.uuid4())

        #==============================================
        #--- create yaml frame | insert variables -----
        #==============================================

        drop = {
                'acquisition': {'groundstation': {'code': code}},
                'creation_dt': timestamp,
                'extent': {
                    'center_dt': timestamp,
                    'coord': {'ll': {'lat': llLat,'lon': llLon}, 
                            'lr': {'lat': lrLat,'lon': lrLon},
                            'ul': {'lat': ulLat,'lon': ulLon},
                            'ur': {'lat': urLat,'lon': urLon}},
                    'from_dt': timestamp,
                    'to_dt': timestamp
                        },
                'format': {'name': 'GeoTIFF'},
                'grid_spatial': {'projection': {'geo_ref_points': {
                        'll': {'x': ulx, 'y': lry}, 
                        'lr': {'x': lrx, 'y': lry},
                        'ul': {'x': ulx, 'y': uly},
                        'ur': {'x': lrx, 'y': uly}
                        },
                        'spatial_reference': PROJCRS
                    }
                },
                'id': id,
                'image': {'bands': {'VH': {'layer': 1, 'path': source_list[0][i]},
                                    'VV': {'layer': 1, 'path': source_list[1][i]}}
                        },
                'instrument': {'name': instrument},
                'lineage': {'source_datasets': {}},
                'platform': {'code': code},
                'processing_level': 'L2',
                'product_type': product_type
        }
        # clear raster      
        raster = None

        # write yaml file
        with open(output + basename[i] + '.yaml', 'w') as f:
            data = yaml.dump(drop, f, width=1000)
        
        print('Yaml ' + str(i + 1)  +' / ' + str(len(source_list[0])) + ' created.')
else:

    for i in range(len(source_list[0])):
        # open raster-file
        raster = gdal.Open(source_list[0][i])

        # load up geo_ref_points » in yaml: x and y
        coords = geo_ref_points(raster) 
        lrx = coords[0]
        lry = coords[1]
        ulx = coords[2]
        uly = coords[3]

        # load up geo_coordinates » in yaml: lat and lon
        info = gdal.Info(raster, format='json')
        geo = list(info['wgs84Extent']['coordinates'])
        llLat = geo[0][1][0]
        llLon = geo[0][1][1]
        lrLat = geo[0][2][0]
        lrLon = geo[0][2][1]
        ulLat = geo[0][0][0]
        ulLon = geo[0][0][1]
        urLat = geo[0][3][0]
        urLon = geo[0][3][1]

        timestring = basename[i].split('_')

        # additional product parameters
        product_type = 'SAR_INT'
        code = 'SENTINEL_1'
        instrument = 'SAR'
        timestamp = format_time_sentinel1(timestring[6])
        PROJCRS = raster.GetProjection()
        id = str(uuid.uuid4())

        #==============================================
        #--- create yaml frame | insert variables -----
        #==============================================

        drop = {
                'acquisition': {'groundstation': {'code': code}},
                'creation_dt': timestamp,
                'extent': {
                    'center_dt': timestamp,
                    'coord': {'ll': {'lat': llLat,'lon': llLon}, 
                            'lr': {'lat': lrLat,'lon': lrLon},
                            'ul': {'lat': ulLat,'lon': ulLon},
                            'ur': {'lat': urLat,'lon': urLon}},
                    'from_dt': timestamp,
                    'to_dt': timestamp
                        },
                'format': {'name': 'GeoTIFF'},
                'grid_spatial': {'projection': {'geo_ref_points': {
                        'll': {'x': ulx, 'y': lry}, 
                        'lr': {'x': lrx, 'y': lry},
                        'ul': {'x': ulx, 'y': uly},
                        'ur': {'x': lrx, 'y': uly}
                        },
                        'spatial_reference': PROJCRS
                    }
                },
                'id': id,
                'image': {'bands': {'ALP': {'layer': 1, 'path': source_list[0][i]},
                                    'ANI': {'layer': 1, 'path': source_list[1][i]},
                                    'ENT': {'layer': 1, 'path': source_list[2][i]}}
                        },
                'instrument': {'name': instrument},
                'lineage': {'source_datasets': {}},
                'platform': {'code': code},
                'processing_level': 'L2',
                'product_type': product_type
        }
        # clear raster      
        raster = None

        # write yaml file
        with open(output + basename[i] + '.yaml', 'w') as f:
            data = yaml.dump(drop, f, width=1000)
        
        print('Yaml ' + str(i + 1)  +' / ' + str(len(source_list[0])) + ' created.')