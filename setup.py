from distutils.core import setup


setup(name='mars2020',
      version='1.0',
      description='An unofficial api',
      author='out-of-cheese-error',
      scripts=["tools/construct_16x16_grid_image"],
      packages=['mars2020'],
      install_requires=["numpy", "requests", "pillow", "scipy", "PySimpleGUI"])
