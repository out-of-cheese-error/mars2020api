import requests as rq
from dataclasses import dataclass
import typing as ty
from PIL import Image


def check_none(dictionary: dict, value: str):
    if value not in dictionary:
        return None
    return None if dictionary[value] == "UNK" else str(dictionary[value])


@dataclass
class ExtendedInfo:
    mast_az: ty.Union[None, str]
    mast_el: ty.Union[None, str]
    sclk: ty.Union[None, str]
    scale_factor: ty.Union[None, float]
    xyz: ty.Union[None, str]
    subframe_rect: ty.Union[None, str]
    dimension: ty.Union[None, ty.Tuple[int, int]]

    @classmethod
    def from_extended_info_dict(cls, extended_info: dict):
        mast_az = check_none(extended_info, "mastAz")
        mast_el = check_none(extended_info, "mastEl")
        sclk = check_none(extended_info, "sclk")
        scale_factor = float(check_none(extended_info, "scaleFactor"))
        xyz = check_none(extended_info, "xyz")
        subframe_rect = check_none(extended_info, "subframeRect")
        x, y = extended_info["dimension"].split(",")
        dimension = (int(x[1:]), int(y[:-1]))
        return cls(mast_az, mast_el, sclk, scale_factor, xyz, subframe_rect, dimension)


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
        camera_model_component_list = check_none(camera_dictionary, "camera_model_component_list")
        camera_position = check_none(camera_dictionary, "camera_position")
        instrument = check_none(camera_dictionary, "instrument")
        camera_model_type = check_none(camera_dictionary, "camera_model_type")
        return cls(filter_name=filter_name,
                   camera_vector=camera_vector,
                   camera_model_component_list=camera_model_component_list,
                   camera_position=camera_position,
                   instrument=instrument,
                   camera_model_type=camera_model_type)


@dataclass
class ImageData:
    camera_type: Camera
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
    earth_date_utc: ty.Union[None, str]
    date_received_on_earth_utc: ty.Union[None, str]

    @classmethod
    def from_image_dictionary(cls, image_dictionary: dict):
        camera: Camera = Camera.from_camera_dictionary(image_dictionary["camera"])
        extended_info: ExtendedInfo = ExtendedInfo.from_extended_info_dict(image_dictionary["extended"])
        image_url = str(image_dictionary["image_files"]["full_res"])
        caption = str(image_dictionary["caption"])
        dimension = extended_info.dimension
        title = image_dictionary["title"]
        image_id = image_dictionary["imageid"]
        attitude = check_none(image_dictionary, "attitude")
        sol = int(check_none(image_dictionary, "sol"))
        mars_date = check_none(image_dictionary, "date_taken_mars")
        earth_date = check_none(image_dictionary, "date_taken_utc")
        date_received_on_earth_utc = check_none(image_dictionary, "date_received")
        sample_type = check_none(image_dictionary, "sample_type")
        return cls(camera_type=camera, image_url=image_url,
                   attitude=attitude, dimension=dimension, caption=caption,
                   title=title, image_id=image_id, sol=sol, mars_date=mars_date,
                   earth_date_utc=earth_date, extended_info=extended_info,
                   date_received_on_earth_utc=date_received_on_earth_utc,
                   sample_type=sample_type)

    @property
    def image_data(self):
        with open("/tmp/nasa_image_temp.png", "wb") as temp_file:
            temp_file.write(
                rq.get(self.image_url).content
            )
        return Image.open("/tmp/nasa_image_temp.png")


@dataclass
class ImageDataCollection:
    images: ty.List[ImageData]
    page_number: ty.Union[None, int]
    number_of_images: ty.Union[None, int]
    total_images_in_database: int

    @classmethod
    def fetch_all_mars2020_imagedata(cls) -> "ImageDataCollection":
        all_data = cls.empty()
        total: int = cls.fetch_partial_mars2020_imagedata(number_of_images=1, page_number=1).total_images_in_database
        for step in range(int(total / 100) + 1):
            all_data += cls.fetch_partial_mars2020_imagedata(number_of_images=100, page_number=step)
        return all_data

    @classmethod
    def empty(cls) -> "ImageDataCollection":
        return cls([], None, 0, 0)

    @classmethod
    def fetch_partial_mars2020_imagedata(cls, number_of_images: int, page_number: int) -> "ImageDataCollection":
        json_data = rq.get(
            f"https://mars.nasa.gov/rss/api/?feed=raw_images&category=mars2020&feedtype=json&num={number_of_images}&page={page_number}").json()
        images: ty.List[ImageData] = [ImageData.from_image_dictionary(x) for x in json_data["images"]]
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
            total_images_in_database=other.total_images_in_database
        )

    def __len__(self):
        return len(self.images)
