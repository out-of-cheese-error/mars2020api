import typing as ty
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests as rq
from PIL import Image
from dateutil.parser import parse as date_parser


def check_none(dictionary: dict, value: str):
    if value not in dictionary:
        return None
    return None if dictionary[value] == "UNK" else str(dictionary[value])


def check_date(dictionary: dict, value: str):
    date_string = check_none(dictionary, value)
    if date_string is not None:
        return date_parser(date_string)
    return None


@dataclass
class ExtendedInfo:
    mast_az: ty.Union[None, str]
    mast_el: ty.Union[None, str]
    scale_factor: ty.Union[None, float]
    xyz: ty.Union[None, ty.Tuple[float, float, float]]
    subframe_rect: ty.Union[None, ty.Tuple[int, int, int, int]]
    dimension: ty.Union[None, ty.Tuple[int, int]]

    @classmethod
    def from_extended_info_dict(cls, extended_info: dict):
        mast_az = check_none(extended_info, "mastAz")
        mast_el = check_none(extended_info, "mastEl")
        scale_factor = check_none(extended_info, "scaleFactor")
        if scale_factor is not None:
            scale_factor = float(scale_factor)
        xyz = check_none(extended_info, "xyz")
        if xyz is not None:
            xyz = tuple(map(float, xyz[1:-1].split(",")))
        subframe_rect = check_none(extended_info, "subframeRect")
        if subframe_rect is not None:
            subframe_rect = tuple(map(int, subframe_rect[1:-1].split(",")))
        dimension = check_none(extended_info, "dimension")
        if dimension is not None:
            dimension = tuple(map(int, dimension[1:-1].split(",")))
        return cls(mast_az, mast_el, scale_factor, xyz, subframe_rect, dimension)


@dataclass
class Camera:
    filter_name: ty.Union[None, str]
    camera_vector: ty.Union[None, str]
    camera_model_component_list: ty.Union[None, ty.List[str]]
    camera_position: ty.Union[None, str]
    instrument: ty.Union[None, str]
    camera_model_type: ty.Union[None, str]

    @classmethod
    def from_camera_dictionary(cls, camera_dictionary: dict):
        filter_name = check_none(camera_dictionary, "filter_name")
        camera_vector = check_none(camera_dictionary, "camera_vector")
        camera_model_component_list = check_none(
            camera_dictionary, "camera_model_component_list"
        )
        camera_position = check_none(camera_dictionary, "camera_position")
        instrument = check_none(camera_dictionary, "instrument")
        camera_model_type = check_none(camera_dictionary, "camera_model_type")
        return cls(
            filter_name=filter_name,
            camera_vector=camera_vector,
            camera_model_component_list=camera_model_component_list,
            camera_position=camera_position,
            instrument=instrument,
            camera_model_type=camera_model_type,
        )


@dataclass
class SpacecraftClockTime:
    sol: int
    spacecraft_clock_time: str
    spacecraft_clock_time_miliseconds: str

    @classmethod
    def from_time_field(cls, sol_code: str, time_code: str, product_code):
        assert len(sol_code) == 4 and len(time_code) == 10 and len(product_code) == 6, (
            sol_code,
            time_code,
            product_code,
        )
        return cls(int(sol_code), time_code, product_code[:3])


@dataclass
class VehicleLocation:
    site_location: str
    site_location_drive_position: str


@dataclass
class InstrumentMeta:
    instrument_identifier: str
    spacecraft_time: SpacecraftClockTime
    filter_number: str
    vehicle_location: VehicleLocation
    thumbnail: bool
    sequence_id: ty.Tuple[str, str]
    product_type_identifier: str
    focal_length: str
    downsampling_factor: int
    jpeg_quality: str
    producer: chr
    version: str

    @classmethod
    def from_image_id(cls, image_id: str):
        # From https://mastcamz.asu.edu/decoding-the-raw-publicly-released-mastcam-z-image-filenames/
        lengths = [3, 4, 10, 3 + 3, 1 + 3 + 4 + 9, 3 + 1 + 2 + 1 + 2]
        index = 0
        codes = []
        for length in lengths:
            codes.append(image_id[index : index + length])
            index += length + 1
        (instrument_code, sol_code, time_code, product_code, code, image_code,) = codes
        instrument_identifier = instrument_code[:2]
        spacecraft_time = SpacecraftClockTime.from_time_field(
            sol_code, time_code, product_code
        )
        filter_number = instrument_code[-1]
        focal_length = image_code[:3]
        downsampling_factor = int(2 ** int(image_code[3]))
        jpeg_quality = image_code[4:6]
        producer = image_code[6]
        version = image_code[-2:]
        product_type_identifier = product_code[-3:]

        thumbnail = code[0] == "T"
        site_location = code[1 : 1 + 3]
        site_location_drive_position = code[4 : 4 + 4]
        sequence_id = (code[8 : 8 + 4], code[8 + 4 : 8 + 4 + 5])
        return cls(
            instrument_identifier=instrument_identifier,
            spacecraft_time=spacecraft_time,
            filter_number=filter_number,
            vehicle_location=VehicleLocation(
                site_location, site_location_drive_position
            ),
            thumbnail=thumbnail,
            sequence_id=sequence_id,
            product_type_identifier=product_type_identifier,
            focal_length=focal_length,
            downsampling_factor=downsampling_factor,
            jpeg_quality=jpeg_quality,
            producer=producer,
            version=version,
        )


@dataclass
class ImageData:
    camera_type: Camera
    instrument_metadata: InstrumentMeta
    extended_info: ExtendedInfo
    image_url: str
    attitude: ty.Union[None, ty.Tuple[float, float, float, float]]
    dimension: ty.Union[None, ty.Tuple[int, int]]
    caption: str
    title: str
    image_id: str
    sol: ty.Union[None, int]
    sample_type: ty.Union[None, str]
    mars_date: ty.Union[None, str]
    earth_date_utc: ty.Union[None, datetime]
    date_received_on_earth_utc: ty.Union[None, datetime]

    @classmethod
    def from_image_dictionary(cls, image_dictionary: dict):
        camera: Camera = Camera.from_camera_dictionary(image_dictionary["camera"])
        extended_info: ExtendedInfo = ExtendedInfo.from_extended_info_dict(
            image_dictionary["extended"]
        )
        image_url = str(image_dictionary["image_files"]["full_res"])
        caption = str(image_dictionary["caption"])
        dimension = extended_info.dimension
        title = image_dictionary["title"]
        image_id = image_dictionary["imageid"]
        attitude = check_none(image_dictionary, "attitude")
        if attitude is not None:
            attitude = tuple(map(float, attitude[1:-1].split(",")))
        sol = int(check_none(image_dictionary, "sol"))
        mars_date = check_none(image_dictionary, "date_taken_mars")
        earth_date = check_date(image_dictionary, "date_taken_utc")
        date_received_on_earth_utc = check_date(image_dictionary, "date_received")
        sample_type = check_none(image_dictionary, "sample_type")
        instrument_metadata = InstrumentMeta.from_image_id(image_id)
        return cls(
            camera_type=camera,
            image_url=image_url,
            attitude=attitude,
            dimension=dimension,
            caption=caption,
            title=title,
            image_id=image_id,
            sol=sol,
            mars_date=mars_date,
            earth_date_utc=earth_date,
            extended_info=extended_info,
            date_received_on_earth_utc=date_received_on_earth_utc,
            sample_type=sample_type,
            instrument_metadata=instrument_metadata,
        )

    @property
    def image_data(self):
        tmp_folder = Path("./tmp")
        if not tmp_folder.exists():
            tmp_folder.mkdir()
        with open(tmp_folder / "nasa_image_temp.png", "wb") as temp_file:
            temp_file.write(rq.get(self.image_url).content)
        return Image.open(tmp_folder / "nasa_image_temp.png")


@dataclass
class ImageDataCollection:
    images: ty.List[ImageData]
    page_number: ty.Union[None, int]
    number_of_images: ty.Union[None, int]
    total_images_in_database: int

    @classmethod
    def fetch_all_mars2020_imagedata(cls) -> "ImageDataCollection":
        all_data = cls.empty()
        total: int = cls.fetch_partial_mars2020_imagedata(
            number_of_images=1, page_number=1
        ).total_images_in_database
        for step in range(int(total / 100) + 1):
            all_data += cls.fetch_partial_mars2020_imagedata(
                number_of_images=100, page_number=step
            )
        return all_data

    @classmethod
    def empty(cls) -> "ImageDataCollection":
        return cls([], None, 0, 0)

    @classmethod
    def fetch_partial_mars2020_imagedata(
        cls, number_of_images: int, page_number: int
    ) -> "ImageDataCollection":
        json_data = rq.get(
            f"https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&num={number_of_images}&page={page_number}"
        ).json()
        images: ty.List[ImageData] = [
            ImageData.from_image_dictionary(x) for x in json_data["images"]
        ]
        total_images_in_database = json_data["total_results"]
        return cls(images, page_number, number_of_images, total_images_in_database)

    @property
    def instrument_names(self) -> ty.Set[str]:
        return {x.camera_type.instrument for x in self.images}

    def __add__(self, other: "ImageDataCollection") -> "ImageDataCollection":
        return ImageDataCollection(
            images=self.images + other.images,
            page_number=None,
            number_of_images=self.number_of_images + other.number_of_images,
            total_images_in_database=other.total_images_in_database,
        )

    def __len__(self):
        return len(self.images)
