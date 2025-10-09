"""
几何工具函数模块
提供几何对象处理、转换和分析的工具函数
"""

import math
from typing import List, Tuple, Union, Optional, Dict, Any
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

    @staticmethod
    def calculate_line_polygon_intersection_ratio(line: LineString, polygon: Polygon) -> float:
        """
        计算线段与多边形的交集比例

        Args:
            line: 线段对象
            polygon: 多边形对象

        Returns:
            float: 交集比例（0.0 - 1.0）
        """
        try:
            # 计算线段与多边形的交集
            intersection = line.intersection(polygon)

            if intersection.is_empty:
                return 0.0

            # 如果交集是线段，计算长度比例
            if hasattr(intersection, 'length') and intersection.length > 0:
                return intersection.length / line.length

            # 如果线段完全包含在多边形内
            if polygon.contains(line):
                return 1.0

            # 如果线段与多边形有接触但无长度交集
            if not intersection.is_empty:
                return 0.01  # 给一个很小的值表示有接触

            return 0.0

        except Exception:
            return 0.0

    @staticmethod
    def calculate_polygon_overlap_ratio(polygon1: Polygon, polygon2: Polygon) -> float:
        """
        计算两个多边形的重叠面积比例

        Args:
            polygon1: 第一个多边形（参考多边形）
            polygon2: 第二个多边形

        Returns:
            float: 重叠面积比例（0.0 - 1.0）
        """
        try:
            # 计算交集面积
            intersection = polygon1.intersection(polygon2)

            if intersection.is_empty or not hasattr(intersection, 'area'):
                return 0.0

            # 计算重叠比例（交集面积 / 第一个多边形的面积）
            if polygon1.area > 0:
                return intersection.area / polygon1.area

            return 0.0

        except Exception:
            return 0.0

    @staticmethod
    def find_best_fit_polygon(geometry: Union[Point, LineString, Polygon],
                            candidate_polygons: List[Polygon],
                            polygon_ids: List[int] = None) -> Tuple[Optional[int], float]:
        """
        为几何对象找到最佳匹配的多边形

        Args:
            geometry: 几何对象（点、线或面）
            candidate_polygons: 候选多边形列表
            polygon_ids: 对应的多边形ID列表（可选）

        Returns:
            Tuple: (最佳匹配多边形ID, 匹配度)
        """
        if not candidate_polygons:
            return None, 0.0

        best_match_id = None
        best_score = 0.0

        if polygon_ids is None:
            polygon_ids = list(range(len(candidate_polygons)))

        # 处理点要素
        if isinstance(geometry, Point):
            for i, polygon in enumerate(candidate_polygons):
                if polygon.contains(geometry) or polygon.touches(geometry):
                    return polygon_ids[i], 1.0

        # 处理线要素
        elif isinstance(geometry, LineString):
            best_ratio = 0.0
            for i, polygon in enumerate(candidate_polygons):
                ratio = GeometryUtils.calculate_line_polygon_intersection_ratio(geometry, polygon)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_id = polygon_ids[i]
            return best_match_id, best_ratio

        # 处理面要素
        elif isinstance(geometry, Polygon):
            best_ratio = 0.0
            for i, polygon in enumerate(candidate_polygons):
                ratio = GeometryUtils.calculate_polygon_overlap_ratio(geometry, polygon)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_id = polygon_ids[i]
            return best_match_id, best_ratio

        return None, 0.0

    @staticmethod
    def calculate_spatial_relationship_stats(geometry1: Union[Point, LineString, Polygon],
                                           geometry2: Union[Point, LineString, Polygon]) -> Dict[str, Any]:
        """
        计算两个几何对象之间的空间关系统计

        Args:
            geometry1: 第一个几何对象
            geometry2: 第二个几何对象

        Returns:
            Dict: 空间关系统计信息
        """
        stats = {
            "contains": False,
            "within": False,
            "intersects": False,
            "touches": False,
            "crosses": False,
            "overlaps": False,
            "intersection_ratio": 0.0,
            "distance": 0.0
        }

        try:
            # 基本空间关系
            stats["contains"] = geometry1.contains(geometry2)
            stats["within"] = geometry1.within(geometry2)
            stats["intersects"] = geometry1.intersects(geometry2)
            stats["touches"] = geometry1.touches(geometry2)
            stats["crosses"] = geometry1.crosses(geometry2)
            stats["overlaps"] = geometry1.overlaps(geometry2)

            # 计算距离
            if not stats["intersects"]:
                stats["distance"] = geometry1.distance(geometry2)
            else:
                stats["distance"] = 0.0

            # 计算交集比例
            intersection = geometry1.intersection(geometry2)
            if not intersection.is_empty:
                if isinstance(geometry1, Point):
                    stats["intersection_ratio"] = 1.0 if stats["contains"] or stats["within"] else 0.0
                elif isinstance(geometry1, LineString):
                    stats["intersection_ratio"] = GeometryUtils.calculate_line_polygon_intersection_ratio(
                        geometry1, geometry2) if isinstance(geometry2, Polygon) else 0.0
                elif isinstance(geometry1, Polygon):
                    if isinstance(geometry2, Polygon):
                        stats["intersection_ratio"] = GeometryUtils.calculate_polygon_overlap_ratio(
                            geometry1, geometry2)
                    elif isinstance(geometry2, LineString):
                        stats["intersection_ratio"] = GeometryUtils.calculate_line_polygon_intersection_ratio(
                            geometry2, geometry1)

        except Exception as e:
            stats["error"] = str(e)

        return stats

    @staticmethod
    def create_buffer_for_spatial_analysis(geometry: Union[Point, LineString, Polygon],
                                         buffer_distance: float) -> Union[Point, LineString, Polygon]:
        """
        为空间分析创建缓冲区

        Args:
            geometry: 几何对象
            buffer_distance: 缓冲距离（米）

        Returns:
            Union: 缓冲区几何对象
        """
        try:
            # 将米转换为度数（粗略转换，在赤道附近）
            distance_degrees = buffer_distance / 111320.0  # 1度 ≈ 111320米

            # 对于点要素，创建圆形缓冲区
            if isinstance(geometry, Point):
                return geometry.buffer(distance_degrees)

            # 对于线要素，创建线缓冲区
            elif isinstance(geometry, LineString):
                return geometry.buffer(distance_degrees)

            # 对于面要素，创建面缓冲区
            elif isinstance(geometry, Polygon):
                return geometry.buffer(distance_degrees)

            return geometry

        except Exception:
            return geometry

    @staticmethod
    def validate_spatial_analysis_inputs(polygons_gdf: gpd.GeoDataFrame,
                                       target_gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        验证空间分析的输入数据

        Args:
            polygons_gdf: 面图层数据
            target_gdf: 目标图层数据

        Returns:
            Dict: 验证结果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {}
        }

        try:
            # 检查面图层
            if polygons_gdf is None or polygons_gdf.empty:
                validation_result["valid"] = False
                validation_result["errors"].append("面图层为空")
                return validation_result

            # 检查面图层几何类型
            polygon_geom_types = polygons_gdf.geometry.geom_type.unique()
            valid_polygon_types = ['Polygon', 'MultiPolygon']
            if not any(geom_type in polygon_geom_types for geom_type in valid_polygon_types):
                validation_result["valid"] = False
                validation_result["errors"].append("面图层不包含有效的面几何类型")
                return validation_result

            # 检查目标图层
            if target_gdf is None or target_gdf.empty:
                validation_result["valid"] = False
                validation_result["errors"].append("目标图层为空")
                return validation_result

            # 检查坐标系
            if polygons_gdf.crs != target_gdf.crs:
                validation_result["warnings"].append("面图层和目标图层的坐标系不一致，可能影响分析精度")

            # 检查数据范围重叠
            polygons_bounds = polygons_gdf.total_bounds
            target_bounds = target_gdf.total_bounds

            # 简单检查边界框是否重叠
            if (polygons_bounds[2] < target_bounds[0] or polygons_bounds[0] > target_bounds[2] or
                polygons_bounds[3] < target_bounds[1] or polygons_bounds[1] > target_bounds[3]):
                validation_result["warnings"].append("面图层和目标图层的空间范围不重叠")

            # 统计信息
            validation_result["info"] = {
                "polygons_count": len(polygons_gdf),
                "target_count": len(target_gdf),
                "target_geom_types": target_gdf.geometry.geom_type.value_counts().to_dict(),
                "polygons_crs": str(polygons_gdf.crs) if polygons_gdf.crs else "未定义",
                "target_crs": str(target_gdf.crs) if target_gdf.crs else "未定义"
            }

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"验证过程中发生错误: {str(e)}")

        return validation_result


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