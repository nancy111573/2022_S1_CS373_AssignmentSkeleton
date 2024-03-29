import math
import sys
from pathlib import Path

from matplotlib import pyplot
from matplotlib.patches import Rectangle

# import our basic, light-weight png reader library
import imageIO.png

'''
A licence plate detection program using adaptive thresholding,  
the step 'get high contrast region by computing standard deviation' is done twice to get more accurate results
'''

# this function reads an RGB color png file and returns width, height, as well as pixel arrays for r,g,b
def readRGBImageToSeparatePixelArrays(input_filename):
    image_reader = imageIO.png.Reader(filename=input_filename)
    # png reader gives us width and height, as well as RGB data in image_rows (a list of rows of RGB triplets)
    (image_width, image_height, rgb_image_rows, rgb_image_info) = image_reader.read()

    print("read image width={}, height={}".format(image_width, image_height))

    # our pixel arrays are lists of lists, where each inner list stores one row of greyscale pixels
    pixel_array_r = []
    pixel_array_g = []
    pixel_array_b = []

    for row in rgb_image_rows:
        pixel_row_r = []
        pixel_row_g = []
        pixel_row_b = []
        r = 0
        g = 0
        b = 0
        for elem in range(len(row)):
            # RGB triplets are stored consecutively in image_rows
            if elem % 3 == 0:
                r = row[elem]
            elif elem % 3 == 1:
                g = row[elem]
            else:
                b = row[elem]
                pixel_row_r.append(r)
                pixel_row_g.append(g)
                pixel_row_b.append(b)

        pixel_array_r.append(pixel_row_r)
        pixel_array_g.append(pixel_row_g)
        pixel_array_b.append(pixel_row_b)

    return (image_width, image_height, pixel_array_r, pixel_array_g, pixel_array_b)


# a useful shortcut method to create a list of lists based array representation for an image, initialized with a value
def createInitializedGreyscalePixelArray(image_width, image_height, initValue=0):
    new_array = [[initValue for x in range(image_width)] for y in range(image_height)]
    return new_array


# Compute greyscale from RGB
def getGreyScale(px_array_r, px_array_g, px_array_b, image_width, image_height):
    greyscale_pixel_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for r in range(image_height):
        for c in range(image_width):
            greyvalue = px_array_r[r][c] * 0.299 + px_array_g[r][c] * 0.587
            greyvalue = round(greyvalue + px_array_b[r][c] * 0.114)
            greyscale_pixel_array[r][c] = greyvalue
    return greyscale_pixel_array


# Stretch to 0 - 255
def stretch(anArray, image_height, image_width):
    stretched_array = createInitializedGreyscalePixelArray(image_width, image_height)
    maximum = minimum = anArray[0][0]
    for r in range(image_height):
        for c in range(image_width):
            if anArray[r][c] > maximum:
                maximum = anArray[r][c]
            elif anArray[r][c] < minimum:
                minimum = anArray[r][c]

    if maximum != minimum:
        a = 255 / (maximum - minimum)
        for r in range(image_height):
            for c in range(image_width):
                stretched_array[r][c] = round((anArray[r][c] - minimum) * a)
    return stretched_array


# computer standard deviation (5 x 5)
def getStandardDeviation(stretched_array, image_width, image_height):
    sd_array = createInitializedGreyscalePixelArray(image_width, image_height, 0)
    for r in range(2, image_height - 2):
        for c in range(2, image_width - 2):
            avg = stretched_array[r - 2][c - 2] + stretched_array[r - 2][c - 1] + stretched_array[r - 2][c] + \
                  stretched_array[r - 2][c + 1] + stretched_array[r - 2][c + 2]
            avg += stretched_array[r - 1][c - 2] + stretched_array[r - 1][c - 1] + stretched_array[r - 1][c] + \
                   stretched_array[r - 1][c + 1] + stretched_array[r - 1][c + 2]
            avg += stretched_array[r][c - 2] + stretched_array[r][c - 1] + stretched_array[r][c] + stretched_array[r][
                c + 1] + stretched_array[r][c + 2]
            avg += stretched_array[r + 1][c - 2] + stretched_array[r + 1][c - 1] + stretched_array[r + 1][c] + \
                   stretched_array[r + 1][c + 1] + stretched_array[r + 1][c + 2]
            avg += stretched_array[r + 2][c - 2] + stretched_array[r + 2][c - 1] + stretched_array[r + 2][c] + \
                   stretched_array[r + 2][c + 1] + stretched_array[r + 2][c + 2]
            avg = avg / 25

            temp = pow(stretched_array[r - 2][c - 1] - avg, 2)
            temp += pow(stretched_array[r - 2][c] - avg, 2) + pow(stretched_array[r - 2][c + 1] - avg, 2)
            temp += pow(stretched_array[r - 1][c - 1] - avg, 2) + pow(stretched_array[r - 1][c] - avg, 2)
            temp += pow(stretched_array[r - 1][c + 1] - avg, 2) + pow(stretched_array[r][c - 1] - avg, 2)
            temp += pow(stretched_array[r][c] - avg, 2) + pow(stretched_array[r][c + 1] - avg, 2)
            temp += pow(stretched_array[r + 1][c - 1] - avg, 2) + pow(stretched_array[r + 1][c] - avg, 2)
            temp += pow(stretched_array[r + 1][c + 1] - avg, 2) + pow(stretched_array[r + 2][c - 1] - avg, 2)
            temp += pow(stretched_array[r + 2][c] - avg, 2) + pow(stretched_array[r + 2][c + 1] - avg, 2)
            temp = temp / 25
            sd_array[r][c] = int(math.sqrt(temp))
    return sd_array


# compute image by threshold to get high contrast area
def getThresholdArray(anArray, image_width, image_height, threshold):
    threshold_array = createInitializedGreyscalePixelArray(image_width, image_height, 0.0)
    for r in range(image_height):
        for c in range(image_width):
            if anArray[r][c] < threshold:
                threshold_array[r][c] = 0
            else:
                threshold_array[r][c] = 255
    return threshold_array


# get non-cumulative histogram from input image (255 bins)
def computeHistogram(pixel_array, image_width, image_height):
    histogram = [0.0 for i in range(256)]
    for r in range(image_height):
        for c in range(image_width):
            histogram[pixel_array[r][c] - 1] += 1
    return histogram


# EXTENSION: calculate adaptive threshold from input image
def getThreshold(anArray, image_height, image_width):
    Hq = computeHistogram(anArray, image_width, image_height)
    qHq = [0.0 for x in range(len(Hq))]
    previous = 0
    for x in range(len(Hq)):
        qHq[x] = x * Hq[x]
    threshold = int(math.ceil(sum(qHq) / sum(Hq)))
    while threshold != previous:
        previous = threshold
        objects = background = NumObjects = NumBackground = 0
        for obj in range(previous):
            NumObjects += Hq[obj]
            objects += qHq[obj]
        for bg in range(previous, len(Hq)):
            NumBackground += Hq[bg]
            background += qHq[bg]
        threshold = int(math.ceil((objects / NumObjects + background / NumBackground) / 2))
    return threshold


# 3x3 dilation
def computeDilation8Nbh3x3FlatSE(pixel_array, image_width, image_height):
    result = createInitializedGreyscalePixelArray(image_width, image_height)
    padding = createInitializedGreyscalePixelArray(image_width + 2, image_height + 2)
    for r in range(image_height):
        for c in range(image_width):
            padding[r + 1][c + 1] = pixel_array[r][c]
    for r in range(image_height):
        for c in range(image_width):
            result[r][c] = 1
            if padding[r][c] == 0 and padding[r + 1][c] == 0 and padding[r + 2][c] == 0:
                if padding[r][c + 1] == 0 and padding[r + 1][c + 1] == 0 and padding[r + 2][c + 1] == 0:
                    if padding[r][c + 2] == 0 and padding[r + 1][c + 2] == 0 and padding[r + 2][c + 2] == 0:
                        result[r][c] = 0
    return result


# 3x3 erosion
def computeErosion8Nbh3x3FlatSE(pixel_array, image_width, image_height):
    result = createInitializedGreyscalePixelArray(image_width, image_height)
    for r in range(1, image_height - 1):
        for c in range(1, image_width - 1):
            if pixel_array[r][c] != 0 and pixel_array[r - 1][c] != 0 and pixel_array[r + 1][c] != 0:
                if pixel_array[r][c - 1] != 0 and pixel_array[r - 1][c - 1] != 0 and pixel_array[r + 1][c - 1] != 0:
                    if pixel_array[r][c + 1] != 0 and pixel_array[r - 1][c + 1] != 0 and pixel_array[r + 1][c + 1] != 0:
                        result[r][c] = 1
    return result


# get connected components
def computeConnectedComponentLabeling(pixel_array, image_width, image_height):
    result = createInitializedGreyscalePixelArray(image_width, image_height)
    components = {}
    visited = {}
    count = 1
    for r in range(image_height):
        for c in range(image_width):
            if pixel_array[r][c] != 0 and (r not in visited or c not in visited[r]):
                queue = []
                queue.append((r, c))
                components[count] = 0
                if r in visited:
                    visited[r].append(c)
                else:
                    visited[r] = [c]
                while len(queue) != 0:
                    (c1, c2) = queue.pop(0)
                    result[c1][c2] = count
                    components[count] += 1

                    if c1 not in visited:
                        if c2 > 0 and pixel_array[c1][c2 - 1] != 0:
                            queue.append((c1, c2 - 1))
                            visited[c1] = [c2 - 1]
                        elif c2 < image_width - 1 and pixel_array[c1][c2 + 1] != 0:
                            queue.append((c1, c2 + 1))
                            visited[c1] = [c2 + 1]
                    elif c2 > 0 and c2 - 1 not in visited[c1] and pixel_array[c1][c2 - 1] != 0:
                        queue.append((c1, c2 - 1))
                        visited[c1].append(c2 - 1)
                    elif c2 < image_width - 1 and c2 + 1 not in visited[c1] and pixel_array[c1][c2 + 1] != 0:
                        queue.append((c1, c2 + 1))
                        visited[c1].append(c2 + 1)

                    if c1 > 0 and pixel_array[c1 - 1][c2] != 0:
                        if c1 - 1 not in visited:
                            queue.append((c1 - 1, c2))
                            visited[c1 - 1] = [c2]
                        elif c2 not in visited[c1 - 1]:
                            queue.append((c1 - 1, c2))
                            visited[c1 - 1].append(c2)
                    if c1 < image_height - 1 and pixel_array[c1 + 1][c2] != 0:
                        if c1 + 1 not in visited:
                            queue.append((c1 + 1, c2))
                            visited[c1 + 1] = [c2]
                        elif c2 not in visited[c1 + 1]:
                            queue.append((c1 + 1, c2))
                            visited[c1 + 1].append(c2)
                count += 1
    return result, components


# License plate detection in this function follows structure given in recording,
# but the step get high contrast region by computing standard deviation is done twice.
# Adaptive thresholding is also used instead of a set threshold
def main():
    command_line_arguments = sys.argv[1:]

    SHOW_DEBUG_FIGURES = True

    # this is the default input image filename
    input_filename = "numberplate1.png"

    if command_line_arguments != []:
        input_filename = command_line_arguments[0]
        SHOW_DEBUG_FIGURES = False

    output_path = Path("output_images")
    if not output_path.exists():
        # create output directory
        output_path.mkdir(parents=True, exist_ok=True)

    output_filename = output_path / Path(input_filename.replace(".png", "_output.png"))
    if len(command_line_arguments) == 2:
        output_filename = Path(command_line_arguments[1])

    # we read in the png file, and receive three pixel arrays for red, green and blue components, respectively
    # each pixel array contains 8 bit integer values between 0 and 255 encoding the color values
    (image_width, image_height, px_array_r, px_array_g, px_array_b) = readRGBImageToSeparatePixelArrays(input_filename)

    # setup the plots for intermediate results in a figure
    fig1, axs1 = pyplot.subplots(2, 2)
    axs1[0, 0].set_title('Input red channel of image')
    axs1[0, 0].imshow(px_array_r, cmap='gray')
    axs1[0, 1].set_title('Input green channel of image')
    axs1[0, 1].imshow(px_array_g, cmap='gray')
    axs1[1, 0].set_title('Input blue channel of image')
    axs1[1, 0].imshow(px_array_b, cmap='gray')

    # STUDENT IMPLEMENTATION here

    greyscale_pixel_array = getGreyScale(px_array_r, px_array_g, px_array_b, image_width, image_height)
    print("greyscale done")
    stretched_array = stretch(greyscale_pixel_array, image_height, image_width)
    print("stretch done")
    # standard deviation done twice to get higher contrast
    sd_array = getStandardDeviation(stretched_array, image_width, image_height)
    second_stretch = stretch(sd_array, image_height, image_width)
    print("standard deviation once")
    sd_array = getStandardDeviation(second_stretch, image_width, image_height)
    second_stretch = stretch(sd_array, image_height, image_width)
    print("standard deviation twice")
    # calculate adaptive threshold
    threshold = getThreshold(second_stretch, image_height, image_width)
    print("calculated adaptive threshold = ", threshold)
    threshold_array = getThresholdArray(second_stretch, image_width, image_height, threshold)
    print("threshold_array done")

    dilated_array = computeDilation8Nbh3x3FlatSE(threshold_array, image_width, image_height)
    for count in range(6):
        dilated_array = computeDilation8Nbh3x3FlatSE(dilated_array, image_width, image_height)
    print("dilation x 7")

    eroded_array = computeErosion8Nbh3x3FlatSE(dilated_array, image_width, image_height)
    for count in range(6):
        eroded_array = computeErosion8Nbh3x3FlatSE(eroded_array, image_width, image_height)
    print("erosion x 7")

    connected_components, components_dictionary = computeConnectedComponentLabeling(eroded_array, image_width, image_height)
    # find biggest connected component where ratio is < 5 and > 1.5
    done = False
    while not done:
        max_key = max(components_dictionary, key=components_dictionary.get)
        maxY = 0
        minY = image_height
        maxX = 0
        minX = image_width
        for r in range(image_height):
            for c in range(image_width):
                if connected_components[r][c] == max_key:
                    if r > maxY:
                        maxY = r
                    elif r < minY:
                        minY = r
                    if c > maxX:
                        maxX = c
                    elif c < minX:
                        minX = c
        ratio = (maxX - minX) / (maxY - minY)
        if ratio > 5 or ratio < 1.5:
            components_dictionary[max_key] = 0
        else:
            done = True
            print("ratio: ", ratio)

    px_array = greyscale_pixel_array

    bbox_min_x = minX
    bbox_max_x = maxX
    bbox_min_y = minY
    bbox_max_y = maxY

    # Draw a bounding box as a rectangle into the input image
    # Final image of detection
    axs1[1, 1].set_title('Final image of detection')
    axs1[1, 1].imshow(px_array, cmap='gray')
    rect = Rectangle((bbox_min_x, bbox_min_y), bbox_max_x - bbox_min_x, bbox_max_y - bbox_min_y, linewidth=1,
                     edgecolor='g', facecolor='none')
    axs1[1, 1].add_patch(rect)

    # write the output image into output_filename, using the matplotlib savefig method
    extent = axs1[1, 1].get_window_extent().transformed(fig1.dpi_scale_trans.inverted())
    pyplot.savefig(output_filename, bbox_inches=extent, dpi=600)

    if SHOW_DEBUG_FIGURES:
        # plot the current figure
        pyplot.show()


if __name__ == "__main__":
    main()
