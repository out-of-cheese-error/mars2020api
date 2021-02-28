# Perseverance Rover Image API

Python API for downloading [NASA's Perseverance Rover](https://mars.nasa.gov) images and metadata.

Combines JSON metadata about the camera and image with 
[image filename metadata](https://mastcamz.asu.edu/decoding-the-raw-publicly-released-mastcam-z-image-filenames/) about the instrument.

## Installation
```sh
pip install git+https://github.com/out-of-cheese-error/mars2020api
```

## Usage

Some imports and a helper function to plot a grid of images:

```python
import PIL
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

from mars2020 import mars2020api

def display_image_grid(images: [mars2020api.ImageData], columns=3, width=15, height=8, max_images=30):
    if len(images) > max_images:
        print(f"Showing {max_images} of {len(images)} images")
        images = images[:max_images]
    height = max(height, int(len(images) / columns) * height)
    plt.figure(figsize=(width, height))
    for i, image in enumerate(images):
        plt.subplot(int(len(images) // columns + 1), columns, i + 1)
        plt.imshow(image.image_data)
        plt.axis("off")
    plt.show()
```

Fetch all of NASA's Mars data (this just gets all the image metadata, the actual images are downloaded lazily when requested)

```python
all_data = mars2020api.ImageDataCollection.fetch_all_mars2020_imagedata()
```

## Collage

During the descent, the EDL_RDCAM camera continously took a ton of pictures that were perfect for collaging together. 

```python
images = [
    x for x in all_data.images 
    if x.camera_type.instrument == "EDL_RDCAM" 
    and not x.instrument_metadata.thumbnail # Not a thumbnail pic
    and x.instrument_metadata.filter_number == "E"
]
len(images)
```

```python
display_image_grid(images[:6])
```

<!-- #region -->
We used Photoshop's Photomerge algorithm (had to subsample to a 100 images to keep Photoshop from crashing) to get this absolute beauty:

![collage EDL_RDCAM Filter E](./images/collage_EDL_RDCAM_E.png)


And similarly for `filter_number = F`:

![collage EDL_RDCAM Filter F](./images/collage_EDL_RDCAM_F.png)
<!-- #endregion -->

## Panorama

<!-- #region -->
NASA released a beautiful [360-degree panorama](https://mars.nasa.gov/resources/25640/mastcam-zs-first-360-degree-panorama/) shot by the Mastcam-Z cameras on board. We tried to replicate this by getting the same images and running it through Photomerge again.


[NASA's claims to have used](https://www.nasa.gov/offices/oct/home/tech_life_gigapan.html) the [GigaPan software](http://gigapan.com/) for this but we couldn't really get this to work probably because of the ordering of the images.
<!-- #endregion -->

```python
images = [
        x
        for x in all_data.images
        if x.camera_type.instrument == "MCZ_LEFT" # MastCam Z - Left
        and not x.instrument_metadata.thumbnail # Not a thumbnail picture
        and x.instrument_metadata.filter_number == "F"
        and x.date_received_on_earth_utc.day == 24 # Received on 24th Feb 2021
    ]
len(images)
```

Here are some results from Photomerge!

![panorama_spherical](./images/panorama_MCZ_LEFT_spherical.jpg)

![panorama](./images/panorama_MCZ_LEFT.jpg)


## RGB


A bunch of the cameras took separate R, G, and B channels for each image. We matched these together with the `camera_vector` information and composited them.

```python
def match_rgb(r_image: mars2020api.ImageData, g_images: [mars2020api.ImageData], b_images: [mars2020api.ImageData]):
    vector = r_image.camera_type.camera_vector
    g_image = [x for x in g_images if x.camera_type.camera_vector == vector]
    if len(g_image) == 0:
        return None
    b_image = [x for x in b_images if x.camera_type.camera_vector == vector]
    if len(b_image) == 0:
        return None
    return (r_image, g_image[0], b_image[0])
```

```python
rgb_matches = []
for cam_type in all_data.instrument_names:
    cam_images = [x for x in all_data.images if x.camera_type.instrument == cam_type and not x.instrument_metadata.thumbnail]
    filters = set(x.instrument_metadata.filter_number for x in cam_images)
    if not set("RGB").difference(filters):
        print(cam_type)
        r_images = [x for x in cam_images if x.instrument_metadata.filter_number == "R"]
        g_images = [x for x in cam_images if x.instrument_metadata.filter_number == "G"]
        b_images = [x for x in cam_images if x.instrument_metadata.filter_number == "B"]
        rgb_matches += [match_rgb(r_image, g_images, b_images) for r_image in r_images]
len(rgb_matches)
```

An example of what that looks like:

![RGB image example](./images/m6.png)


See the rest, as well as high-res versions of all of the above in [this Flickr album](https://flic.kr/s/aHsmUybm5N)

Visit our [blog post](https://out-of-cheese-error.netlify.app/perseverance) for more details .