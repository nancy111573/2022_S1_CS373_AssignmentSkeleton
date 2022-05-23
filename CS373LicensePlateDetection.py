import math
import sys
from pathlib import Path

from matplotlib import pyplot
from matplotlib.patches import Rectangle

# import our basic, light-weight png reader library
import imageIO.png


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
    sd_array = createInitializedGreyscalePixelArray(image_width, image_height, 0.0)
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
            sd_array[r][c] = math.sqrt(temp)
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
            histogram[pixel_array[r][c]-1] += 1
    return histogram

# EXTENSION: calculate threshold from input image
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
        threshold = int(math.ceil((objects/NumObjects + background/NumBackground)/2))
    return threshold


# This is our code skeleton that performs the license plate detection.
# Feel free to try it on your own images of cars, but keep in mind that with our algorithm developed in this lecture,
# we won't detect arbitrary or difficult to detect license plates!
def main():
    command_line_arguments = sys.argv[1:]

    SHOW_DEBUG_FIGURES = True

    # this is the default input image filename
    input_filename = "numberplate6.png"

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
    fig1, axs1 = pyplot.subplots(3, 2)
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

    sd_array = getStandardDeviation(stretched_array, image_width, image_height)
    print("standard deviation done")

    # stretch high contrast image to 0 to 255 range
    secondStretch = stretch(sd_array, image_height, image_width)
    print("stretched again")

    # calculate threshold
    threshold = getThreshold(greyscale_pixel_array, image_height, image_width)
    print("calculated threshold = ", threshold)

    threshold_array = getThresholdArray(secondStretch, image_width, image_height, threshold)
    print("threshold_array done")

    #  STUDENT IMPLEMENTATION END

    oneFivty = getThresholdArray(secondStretch, image_width, image_height, 150)
    px_array = threshold_array

    # compute a dummy bounding box centered in the middle of the input image, and with as size of half of width and height
    center_x = image_width / 2.0
    center_y = image_height / 2.0
    bbox_min_x = center_x - image_width / 4.0
    bbox_max_x = center_x + image_width / 4.0
    bbox_min_y = center_y - image_height / 4.0
    bbox_max_y = center_y + image_height / 4.0

    # Draw a bounding box as a rectangle into the input image
    # Final image of detection
    axs1[1, 1].set_title('adaptive threshold')
    axs1[1, 1].imshow(px_array, cmap='gray')
    rect = Rectangle((bbox_min_x, bbox_min_y), bbox_max_x - bbox_min_x, bbox_max_y - bbox_min_y, linewidth=1,
                     edgecolor='g', facecolor='none')
    axs1[1, 1].add_patch(rect)

    # Draw threshold = 150
    axs1[2, 1].set_title('150 threshold')
    axs1[2, 1].imshow(oneFivty, cmap='gray')

    # write the output image into output_filename, using the matplotlib savefig method
    extent = axs1[1, 1].get_window_extent().transformed(fig1.dpi_scale_trans.inverted())
    pyplot.savefig(output_filename, bbox_inches=extent, dpi=600)

    if SHOW_DEBUG_FIGURES:
        # plot the current figure
        pyplot.show()


if __name__ == "__main__":
    main()
