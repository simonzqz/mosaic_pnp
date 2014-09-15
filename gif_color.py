###################################################################
#  09/13/2014 Simon Zhang
#  copy right 2014
#  read in the image gif file, and output G-code file
###################################################################

from PIL import Image

###################################################################
# utility function to compare the color
# a[3] is the color array RGB
# b[3] is the color array RGB
# return 0 if it is the same color
# return -1 if a > b
# return 1 if a < b
def compare (a, b):
    if (a[0] > b[0]):
        return -1
    elif (a[0] < b[0]):
        return 1
    elif(a[1] > b[1]):
        return -1
    elif (a[1] < b[1]):
        return 1
    elif (a[2] > b[2]):
        return -1
    elif (a[2] < b[2]):
        return 1
    else:
        return 0

    
###################################################################
# the util function to insert one color (RGB) to the list
def insert_color (color_list, color, num_color):
    tmp = []
    if (num_color):
        tmp.append(color[0])
        tmp.append(color[1])
        tmp.append(color[2])
        tmp.append(num_color)
        color_list.append(tmp)

        
####################################################################
#get the color list from the pixel_list
#return the color list
def get_color_list (pixel_list, color_list):
    prev_pixel=[-1, -1, -1]
    num_of_same_color = 0
    color_count = 0
    for pixel in pixel_list:
    
        if (compare(prev_pixel, pixel) != 0):
            #print "prev_pixel:{0:d} {1:d} {2:d}\n".format(\
            #         prev_pixel[0],prev_pixel[1],prev_pixel[2])
            #print "pixel:{0:d} {1:d} {2:d}\n".format(\
            #         pixel[0],pixel[1],pixel[2])
        
            insert_color(color_list, prev_pixel, num_of_same_color)
            num_of_same_color = 0
            color_count = color_count + 1
        
        else:
            num_of_same_color = num_of_same_color + 1
        prev_pixel = pixel


    #last color if any
    if (num_of_same_color > 0):
        insert_color(color_list, prev_pixel, num_of_same_color)
    return color_count

#######################################################################
def color_index (color_list, r, g, b):
    index = -1
    i = 0
    for item in color_list:
        if (item[0] == r and item[1] == g and item[2] == b):
            return i
        i = i+ 1
    return index

#########################################################################
def get_index_cnc_coord (index):
    x = -15.403 + index * 0.67
    return (x)

#######################################################################
def get_tile_cnc_coord (x):
    xx = x * 0.67
    return (xx)

########################################################################
def get_tile_gcode(tile_index, tile_size, width, hight,
                   color_list, rgb_im, tile):
    
    max_column = (width - 1) / tile_size + 1
    #max_y = (hight - 1) / tile_size + 1
    x_base = (tile_index % max_column ) * tile_size
    y_base = (tile_index / max_column) * tile_size

    #print ("max_column %d x_base %d y_base %d tile_index %d" % (\
    #    max_column, x_base, y_base, tile_index))
    for y in range (0, tile_size):
        for x in range (0, tile_size):
            xx = x + x_base;
            if (xx >= width):
                continue
            yy = y + y_base;
            if (yy >= hight):
                continue
            #print (" x %d y %d" % (xx, hight - 1 - yy))
            r, g, b = rgb_im.getpixel((xx, hight - 1 - yy))
            index = color_index(color_list, r, g, b)
            
            #mosaic color library
            tile.append("G0X%.3fY%.3f\n"%(get_index_cnc_coord(index), 15.488))

            #picture 
            tile.append("G0X%.3fY%.3f\n"%(get_tile_cnc_coord(x),
                                 get_tile_cnc_coord(y)))
    
#########################################################################
def output_constant (f, const):
    for item in const:
        f.write(item)

#########################################################################
# Main function
#
name = raw_input("enter the image file name:")
print "{}".format(name)
im = Image.open(name) #Can be many different formats.
pix = im.load()

#Get the width and hight of the image for iterating over
width, hight = im.size


total_num_color = 0
color_list = [] # sorted color list whith 3 rgb colors and num of pixel
pixel_color_list = [] # all non sorted pixel list

rgb_im = im.convert('RGB')
f = open(name+".txt",'w+')
f.write(name)
f.write(" image size: width={0:5d} high={1:5d}\n".format(width,hight))
f.write("  width hight:   r     g     b \n")
for j in range(0,hight):
    for i in range(0,width):
        r, g, b = rgb_im.getpixel((i, hight - 1 - j))
        f.write("{0:5d}, {1:5d}, {2:5d}, {3:5d}, {4:5d}\n".format(i,j,r,g,b))

        # get the pixel color RGB
        tmp_color_list = []
        tmp_color_list.append(r)
        tmp_color_list.append(g)
        tmp_color_list.append(b)
        tmp_color_list.append(i)
        tmp_color_list.append(j)

        # insert the pixel into pixel_color_list for the future use
        pixel_color_list.append(tmp_color_list)
f.close()

# sort the pixel_color_list
pixel_color_list.sort(compare)

# get the color_list
total_num_color = get_color_list(pixel_color_list, color_list)

print "number of color %d\n"%(total_num_color)

f = open(name+".color.txt",'w+')
f.write(name)
f.write(" number of color {0:d}\n".format(len(color_list)))
f.write(" color (RGB) number of pixel\n")
for index, item in enumerate(color_list):
    f.write("%.3f,  %.3f,   " % (get_index_cnc_coord(index), 15.488))
            
    f.write("{0:4d}, {1:4d}, {2:4d}, {3:8d}\n".format(\
        item[0],item[1],item[2],item[3]))
f.close()    

#G_CODE header, footer and Tiling area
header_list=["M3\n","G0Z0.000\n","G0X0.000Y0.000\n"]
footer_list=["G0X0.000Y0.000\n","M30\n"]
tiling_list=["G0Z-1.000\n","G0Z0.000\n"]
tile_size = 18

tile_count = ((width - 1) / tile_size + 1) * ((hight - 1) / tile_size + 1)

print "width %d hight %d has %d tile" %(width, hight, tile_count)

tile_list = []
for i in range(0, tile_count):
    tile = []
    get_tile_gcode(i, tile_size, width, hight, color_list, rgb_im, tile)
    tile_list.append(tile)
    #for item in tile:
    #    print item


for cell_index, tile in enumerate(tile_list):
    f = open(name+".gcode_{:03d}.txt" .format(cell_index),'w+')

    #output header
    output_constant(f, header_list)
    
    for tile_index, item in enumerate(tile):
        f.write(item)

        #output tiling area
        output_constant(f, tiling_list)

    #output footer
    output_constant(f, footer_list)    
    f.close()
