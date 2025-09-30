"""
几何工具函数模块
提供几何对象处理、转换和分析的工具函数
"""

import math
from typing import List, Tuple, Union, Optional
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from shapely.ops import transform, unary_union
import geopandas as gpd
import pandas as pd


class GeometryUtils:
    """几何工具类"""

    EARTH_RADIUS_KM = 6371.0  # 地球半径（千米）
    EARTH_RADIUS_M = 6371000.0  # 地球半径（米）

    @staticmethod
    def calculate_distance_point_to_point(point1: Point, point2: Point, method: str = "haversine") -> float:
        """
        计算两点之间的距离

        Args:
            point1: 起始点
            point2: 终点
            method: 计算方法 ("haversine" 或 "euclidean")

        Returns:
            float: 距离（千米）
        """
        lon1, lat1 = point1.x, point1.y
        lon2, lat2 = point2.x, point2.y

        if method == "haversine":
            # 使用Haversine公式计算球面距离
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)

            a = (math.sin(delta_lat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
            c = 2 * math.asin(math.sqrt(a))

            return GeometryUtils.EARTH_RADIUS_KM * c
        else:
            # 使用欧几里得距离
            return math.sqrt((lon2 - lon1) ** 2 + (lat2 - lat1) ** 2)

    @staticmethod
    def calculate_line_length(line: LineString) -> float:
        """
        计算线段长度

        Args:
            line: 线段对象

        Returns:
            float: 长度（千米）
        """
        total_length = 0.0
        coords = list(line.coords)

        for i in range(len(coords) - 1):
            point1 = Point(coords[i])
            point2 = Point(coords[i + 1])
            total_length += GeometryUtils.calculate_distance_point_to_point(point1, point2)

        return total_length

    @staticmethod
    def calculate_polygon_area(polygon: Polygon) -> float:
        """
        计算多边形面积（近似值）

        Args:
            polygon: 多边形对象

        Returns:
            float: 面积（平方千米）
        """
        # 使用Shapely的area方法，然后转换为平方千米
        # 注意：这里使用的是平面面积计算，对于大范围区域可能不准确
        area_degrees = polygon.area

        # 近似转换：1度平方 ≈ 111.32公里平方（在赤道附近）
        # 这只是一个粗略的估算
        area_km2 = area_degrees * (111.32 ** 2)

        return area_km2

    @staticmethod
    def get_geometry_bounds(geometry: Union[Point, LineString, Polygon]) -> Tuple[float, float, float, float]:
        """
        获取几何对象的边界框

        Args:
            geometry: 几何对象

        Returns:
            Tuple: (最小经度, 最小纬度, 最大经度, 最大纬度)
        """
        bounds = geometry.bounds
        return bounds[0], bounds[1], bounds[2], bounds[3]

    @staticmethod
    def is_point_in_polygon(point: Point, polygon: Polygon) -> bool:
        """
        判断点是否在多边形内部

        Args:
            point: 点对象
            polygon: 多边形对象

        Returns:
            bool: 是否在内部
        """
        return polygon.contains(point) or polygon.touches(point)

    @staticmethod
    def buffer_geometry(geometry: Union[Point, LineString, Polygon], distance: float) -> Union[Point, LineString, Polygon]:
        """
        为几何对象创建缓冲区

        Args:
            geometry: 几何对象
            distance: 缓冲距离（千米）

        Returns:
            Union: 缓冲区几何对象
        """
        # 将千米转换为度数（粗略转换）
        distance_degrees = distance / 111.32

        return geometry.buffer(distance_degrees)

    @staticmethod
    def simplify_geometry(geometry: Union[LineString, Polygon], tolerance: float) -> Union[LineString, Polygon]:
        """
        简化几何对象

        Args:
            geometry: 几何对象
            tolerance: 简化容差（度数）

        Returns:
            Union: 简化后的几何对象
        """
        return geometry.simplify(tolerance, preserve_topology=True)

    @staticmethod
    def convert_geometry_to_wkt(geometry: Union[Point, LineString, Polygon]) -> str:
        """
        将几何对象转换为WKT格式

        Args:
            geometry: 几何对象

        Returns:
            str: WKT格式字符串
        """
        return geometry.wkt

    @staticmethod
    def create_bounding_box_from_points(points: List[Point]) -> Polygon:
        """
        从点列表创建边界框

        Args:
            points: 点列表

        Returns:
            Polygon: 边界框多边形
        """
        if not points:
            raise ValueError("点列表不能为空")

        min_x = min(point.x for point in points)
        min_y = min(point.y for point in points)
        max_x = max(point.x for point in points)
        max_y = max(point.y for point in points)

        # 创建边界框
        bbox_coords = [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
            (min_x, min_y)
        ]

        return Polygon(bbox_coords)

    @staticmethod
    def calculate_centroid(geometry: Union[Point, LineString, Polygon]) -> Point:
        """
        计算几何对象的质心

        Args:
            geometry: 几何对象

        Returns:
            Point: 质心点
        """
        return geometry.centroid

    @staticmethod
    def validate_geometry(geometry: Union[Point, LineString, Polygon]) -> List[str]:
        """
        验证几何对象的有效性

        Args:
            geometry: 几何对象

        Returns:
            List[str]: 错误信息列表，空列表表示有效
        """
        errors = []

        # 检查几何对象是否为空
        if geometry.is_empty:
            errors.append("几何对象为空")

        # 检查几何对象是否有效
        if not geometry.is_valid:
            errors.append("几何对象无效")

        # 检查坐标范围
        if isinstance(geometry, Point):
            x, y = geometry.x, geometry.y
            if not (-180 <= x <= 180):
                errors.append(f"经度超出范围: {x}")
            if not (-90 <= y <= 90):
                errors.append(f"纬度超出范围: {y}")

        elif isinstance(geometry, (LineString, Polygon)):
            coords = list(geometry.coords)
            for i, (x, y) in enumerate(coords):
                if not (-180 <= x <= 180):
                    errors.append(f"第 {i+1} 个点经度超出范围: {x}")
                if not (-90 <= y <= 90):
                    errors.append(f"第 {i+1} 个点纬度超出范围: {y}")

        return errors

    @staticmethod
    def merge_polygons(polygons: List[Polygon]) -> Polygon:
        """
        合并多个多边形

        Args:
            polygons: 多边形列表

        Returns:
            Polygon: 合并后的多边形
        """
        if not polygons:
            raise ValueError("多边形列表不能为空")

        return unary_union(polygons)

    @staticmethod
    def intersect_geometries(geom1: Union[Point, LineString, Polygon],
                           geom2: Union[Point, LineString, Polygon]) -> Optional[Union[Point, LineString, Polygon]]:
        """
        计算两个几何对象的交集

        Args:
            geom1: 第一个几何对象
            geom2: 第二个几何对象

        Returns:
            Union: 交集几何对象，如果没有交集返回None
        """
        intersection = geom1.intersection(geom2)
        return intersection if not intersection.is_empty else None

    @staticmethod
    def get_geometry_type(geometry: Union[Point, LineString, Polygon]) -> str:
        """
        获取几何对象类型

        Args:
            geometry: 几何对象

        Returns:
            str: 几何类型名称
        """
        return type(geometry).__name__

    @staticmethod
    def calculate_summary_statistics(gdf: gpd.GeoDataFrame) -> dict:
        """
        计算几何数据统计摘要

        Args:
            gdf: GeoDataFrame对象

        Returns:
            dict: 统计摘要
        """
        stats = {
            "total_features": len(gdf),
            "geometry_types": {},
            "bounds": None,
            "coordinate_stats": {}
        }

        # 统计几何类型
        for geom in gdf.geometry:
            geom_type = GeometryUtils.get_geometry_type(geom)
            stats["geometry_types"][geom_type] = stats["geometry_types"].get(geom_type, 0) + 1

        # 计算总边界框
        if len(gdf) > 0:
            total_bounds = gdf.total_bounds
            stats["bounds"] = {
                "min_x": total_bounds[0],
                "min_y": total_bounds[1],
                "max_x": total_bounds[2],
                "max_y": total_bounds[3]
            }

        # 计算坐标统计
        all_coords = []
        for geom in gdf.geometry:
            if isinstance(geom, Point):
                all_coords.append((geom.x, geom.y))
            else:
                all_coords.extend(list(geom.coords))

        if all_coords:
            x_coords = [coord[0] for coord in all_coords]
            y_coords = [coord[1] for coord in all_coords]

            stats["coordinate_stats"] = {
                "x_range": (min(x_coords), max(x_coords)),
                "y_range": (min(y_coords), max(y_coords)),
                "x_center": (min(x_coords) + max(x_coords)) / 2,
                "y_center": (min(y_coords) + max(y_coords)) / 2
            }

        return stats


if __name__ == "__main__":
    # 测试代码
    utils = GeometryUtils()

    # 创建测试几何对象
    point1 = Point(116.404, 39.915)  # 北京
    point2 = Point(121.474, 31.230)  # 上海

    # 测试距离计算
    distance = utils.calculate_distance_point_to_point(point1, point2)
    print(f"北京到上海的距离: {distance:.2f} 千米")

    # 创建测试线段
    line = LineString([(116.404, 39.915), (116.405, 39.916), (116.406, 39.917)])
    line_length = utils.calculate_line_length(line)
    print(f"线段长度: {line_length:.6f} 千米")

    # 创建测试多边形
    polygon_coords = [(116.404, 39.915), (116.405, 39.915),
                     (116.405, 39.916), (116.404, 39.916), (116.404, 39.915)]
    polygon = Polygon(polygon_coords)
    polygon_area = utils.calculate_polygon_area(polygon)
    print(f"多边形面积: {polygon_area:.8f} 平方千米")

    # 测试边界框
    bounds = utils.get_geometry_bounds(polygon)
    print(f"边界框: {bounds}")

    # 测试质心
    centroid = utils.calculate_centroid(polygon)
    print(f"质心: {centroid}")

    # 测试几何验证
    errors = utils.validate_geometry(polygon)
    print(f"验证错误: {errors}")

    print("几何工具函数测试完成")