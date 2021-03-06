import typing as ty
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import requests as rq


Coordinate = ty.Tuple[float, float]


@dataclass
class PointProperties:
    sol: int
    roll_degree: float
    pitch_degree: float
    yaw_degree: float
    site_position: str
    distance_km: float
    drive_type: str


class ElementType(Enum):
    Feature = "feature"
    Other = "other"

    @classmethod
    def from_string(cls, string: str) -> "ElementType":
        if string.lower() == "feature":
            return cls.Feature
        return cls.Other


class GeometryType(Enum):
    Point = "point"
    Other = "other"

    @classmethod
    def from_string(cls, string: str) -> "GeometryType":
        if string.lower() == "point":
            return cls.Point
        return cls.Other


@dataclass
class Geometry:
    geometry_type: GeometryType
    coordinate: Coordinate


@dataclass
class Element:
    element_type: ElementType
    properties: PointProperties
    geometry: Geometry

    @classmethod
    def from_element_dict(cls, element_dict):
        element_type: ElementType = ElementType.from_string(element_dict["type"])
        dict_properties: ty.Dict[str, str] = element_dict["properties"]
        properties: PointProperties = PointProperties(
            sol=int(dict_properties["sol"]),
            roll_degree=float(dict_properties["roll_deg"]),
            pitch_degree=float(dict_properties["pitch_deg"]),
            yaw_degree=float(dict_properties["yaw_deg"]),
            site_position=dict_properties["site_pos"],
            distance_km=float(dict_properties["dist_km"]),
            drive_type=dict_properties["drivetype"]
        )
        geometry: Geometry = Geometry(GeometryType.from_string(element_dict["geometry"]["type"]),
                                      coordinate=tuple(map(float, element_dict["geometry"]["coordinates"])))
        return cls(element_type=element_type,
                   properties=properties,
                   geometry=geometry)


Elements = ty.Iterable[Element]


@dataclass
class PathProperties:
    length: float
    id: str
    fromRMC: str
    toRMC: str


@dataclass
class Path:
    coordinates: ty.List[Coordinate]
    properties: PathProperties

    @classmethod
    def from_path_dict(cls, path_dict: dict):
        properties: PathProperties = PathProperties(length=float(path_dict["properties"]["length"]),
                                                    id=path_dict["properties"]["Id"],
                                                    fromRMC=path_dict["properties"]["fromRMC"],
                                                    toRMC=path_dict["properties"]["toRMC"])
        coordinates: ty.List[Coordinate] = [tuple(x) for x in path_dict["geometry"]["coordinates"]]
        return Path(coordinates, properties)


def load_elements() -> Elements:
    waypoints = rq.get("https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json").json()["features"]
    return (Element.from_element_dict(element) for element in waypoints)


Paths = ty.Iterable[Path]


def load_paths() -> Paths:
    paths = rq.get("https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json").json()["features"]
    return (Path.from_path_dict(path) for path in paths)
