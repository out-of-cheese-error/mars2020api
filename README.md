# Perseverance Rover Image API

Python API for downloading [NASA's Perseverance Rover](https://mars.nasa.gov) images and metadata.

Combines JSON metadata about the camera and image with 
[image filename metadata](https://mastcamz.asu.edu/decoding-the-raw-publicly-released-mastcam-z-image-filenames/) about the instrument.

See [`example.ipynb`](./example.ipynb) for usage.

[`RGB.ipynb`](./RGB.ipynb) demonstrates how to filter and match R, G, B raw images to generate a colored image.