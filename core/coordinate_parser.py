"""
坐标解析器模块
解析字符串格式的坐标数据并转换为几何对象
"""

import json
import re
from typing import List, Tuple, Union, Optional, Any
import pandas as pd
from shapely.geometry import Point, LineString, Polygon, GeometryCollection
from shapely.wkt import loads as wkt_loads


class CoordinateParser:
    """坐标解析器类"""

    def __init__(self):
        """初始化坐标解析器"""
        self.coordinate_pattern = re.compile(r'\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]')

    def parse_coordinate_string(self, coord_str: str) -> List[Tuple[float, float]]:
        """
        解析坐标字符串

        Args:
            coord_str: 坐标字符串，格式如 "[[1,1],[2,2]...]"

        Returns:
            List[Tuple[float, float]]: 坐标点列表

        Raises:
            ValueError: 坐标格式错误时抛出异常
        """
        if not coord_str or not isinstance(coord_str, str):
            raise ValueError("坐标字符串不能为空")

        try:
            # 尝试使用JSON解析
            coords = json.loads(coord_str)
            if isinstance(coords, list):
                return [(float(point[0]), float(point[1])) for point in coords]
        except (json.JSONDecodeError, ValueError, IndexError, TypeError):
            # 如果JSON解析失败，使用正则表达式解析
            matches = self.coordinate_pattern.findall(coord_str)
            if matches:
                return [(float(x), float(y)) for x, y in matches]

        raise ValueError(f"无法解析坐标字符串: {coord_str}")

    def detect_geometry_type(self, coords: List[Tuple[float, float]]) -> str:
        """
        根据坐标点数量检测几何类型

        Args:
            coords: 坐标点列表

        Returns:
            str: 几何类型 (Point, LineString, Polygon)
        """
        if not coords:
            return "Unknown"

        if len(coords) == 1:
            return "Point"
        elif len(coords) == 2:
            return "LineString"
        else:
            # 检查是否为闭合多边形
            if len(coords) >= 3:
                first, last = coords[0], coords[-1]
                if abs(first[0] - last[0]) < 1e-10 and abs(first[1] - last[1]) < 1e-10:
                    return "Polygon"
                else:
                    return "LineString"
            return "LineString"

    def create_geometry(self, coords: List[Tuple[float, float]], geometry_type: str = "auto") -> Union[Point, LineString, Polygon]:
        """
        根据坐标点创建几何对象

        Args:
            coords: 坐标点列表
            geometry_type: 指定的几何类型，"auto"为自动检测

        Returns:
            Union[Point, LineString, Polygon]: 几何对象

        Raises:
            ValueError: 坐标点不足或几何类型不匹配时抛出异常
        """
        if not coords:
            raise ValueError("坐标点列表不能为空")

        # 自动检测几何类型
        if geometry_type == "auto":
            geometry_type = self.detect_geometry_type(coords)

        # 创建几何对象
        if geometry_type == "Point":
            if len(coords) != 1:
                raise ValueError("Point类型只需要一个坐标点")
            return Point(coords[0])
        elif geometry_type == "LineString":
            if len(coords) < 2:
                raise ValueError("LineString类型至少需要两个坐标点")
            return LineString(coords)
        elif geometry_type == "Polygon":
            if len(coords) < 3:
                raise ValueError("Polygon类型至少需要三个坐标点")

            # 确保多边形是闭合的
            first, last = coords[0], coords[-1]
            if abs(first[0] - last[0]) >= 1e-10 or abs(first[1] - last[1]) >= 1e-10:
                coords = coords + [coords[0]]

            return Polygon(coords)
        else:
            raise ValueError(f"不支持的几何类型: {geometry_type}")

    def parse_dataframe_column(self, df: pd.DataFrame, column_name: str, geometry_type: str = "auto") -> List[Union[Point, LineString, Polygon]]:
        """
        解析DataFrame中的坐标列

        Args:
            df: 包含坐标数据的DataFrame
            column_name: 坐标列名
            geometry_type: 几何类型，"auto"为自动检测

        Returns:
            List[Union[Point, LineString, Polygon]]: 几何对象列表

        Raises:
            ValueError: 列不存在或解析失败时抛出异常
        """
        if column_name not in df.columns:
            raise ValueError(f"列 '{column_name}' 不存在")

        geometries = []
        failed_count = 0

        for idx, coord_str in enumerate(df[column_name]):
            try:
                # 使用更安全的空值检查
                if coord_str is None or (isinstance(coord_str, float) and pd.isna(coord_str)):
                    geometries.append(None)
                    continue
                elif coord_str == "":
                    geometries.append(None)
                    continue

                coords = self.parse_coordinate_string(str(coord_str))
                geometry = self.create_geometry(coords, geometry_type)
                geometries.append(geometry)

            except Exception as e:
                print(f"解析第 {idx + 1} 行坐标失败: {e}")
                geometries.append(None)
                failed_count += 1

        if failed_count > 0:
            print(f"警告: 共有 {failed_count} 个坐标点解析失败")

        return geometries

    def analyze_column_patterns(self, df: pd.DataFrame, column_name: str, sample_size: int = 100, debug: bool = False) -> dict:
        """
        分析坐标列的数据模式

        Args:
            df: 包含坐标数据的DataFrame
            column_name: 坐标列名
            sample_size: 采样大小
            debug: 是否输出调试信息

        Returns:
            dict: 分析结果
        """
        if column_name not in df.columns:
            raise ValueError(f"列 '{column_name}' 不存在")

        # 采样数据
        sample_data = df[column_name].dropna().head(sample_size)

        if debug:
            print(f"DEBUG: 分析字段 '{column_name}'")
            print(f"DEBUG: 总样本数: {len(sample_data)}")
            print(f"DEBUG: 数据类型: {df[column_name].dtype}")

        geometry_types = {"Point": 0, "LineString": 0, "Polygon": 0, "Unknown": 0}
        coord_counts = []
        error_count = 0
        debug_samples = []

        for i, coord_str in enumerate(sample_data):
            try:
                coord_str_clean = str(coord_str).strip()
                if debug and i < 3:  # 只显示前3个样本的调试信息
                    print(f"DEBUG: 样本{i+1}: '{coord_str_clean[:50]}...' (长度: {len(coord_str_clean)})")

                coords = self.parse_coordinate_string(coord_str_clean)
                geom_type = self.detect_geometry_type(coords)

                if debug and i < 3:
                    print(f"DEBUG: 解析结果 - 坐标数: {len(coords)}, 类型: {geom_type}")

                geometry_types[geom_type] += 1
                coord_counts.append(len(coords))

                if debug and i < 3:
                    debug_samples.append({
                        'original': coord_str_clean,
                        'coords_count': len(coords),
                        'type': geom_type
                    })

            except Exception as e:
                error_count += 1
                if debug and i < 3:
                    print(f"DEBUG: 解析失败 - 错误: {e}")

        # 计算统计信息
        if coord_counts:
            avg_coords = sum(coord_counts) / len(coord_counts)
            min_coords = min(coord_counts)
            max_coords = max(coord_counts)
        else:
            avg_coords = min_coords = max_coords = 0

        # 确定主要几何类型
        if sum(geometry_types.values()) > 0:
            main_type = max(geometry_types.items(), key=lambda x: x[1])[0]
        else:
            main_type = "Unknown"

        if debug:
            print(f"DEBUG: 几何类型分布: {geometry_types}")
            print(f"DEBUG: 主要类型: {main_type}")
            print(f"DEBUG: 错误数: {error_count}")

        result = {
            "total_samples": len(sample_data),
            "error_count": error_count,
            "geometry_types": geometry_types,
            "main_geometry_type": main_type,
            "coordinate_stats": {
                "average": avg_coords,
                "minimum": min_coords,
                "maximum": max_coords
            },
            "success_rate": 1 - (error_count / len(sample_data)) if len(sample_data) > 0 else 0
        }

        if debug:
            result['_debug_samples'] = debug_samples

        return result

    def validate_coordinates(self, coords: List[Tuple[float, float]]) -> List[str]:
        """
        验证坐标数据的合法性

        Args:
            coords: 坐标点列表

        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []

        if not coords:
            errors.append("坐标点列表为空")
            return errors

        # 检查坐标范围
        for i, (x, y) in enumerate(coords):
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                errors.append(f"第 {i+1} 个坐标点包含非数值数据: ({x}, {y})")

            # 检查经纬度范围
            if not (-180 <= x <= 180):
                errors.append(f"第 {i+1} 个坐标点经度超出范围 (-180 to 180): {x}")
            if not (-90 <= y <= 90):
                errors.append(f"第 {i+1} 个坐标点纬度超出范围 (-90 to 90): {y}")

        # 检查重复点
        if len(coords) > 1:
            unique_coords = set(coords)
            if len(unique_coords) < len(coords):
                errors.append("坐标列表中存在重复点")

        return errors


if __name__ == "__main__":
    # 测试代码
    parser = CoordinateParser()

    # 测试坐标字符串解析
    test_strings = [
        "[[116.404, 39.915]]",  # 点
        "[[116.404, 39.915], [116.405, 39.916]]",  # 线
        "[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917], [116.404, 39.915]]"  # 面
    ]

    for i, coord_str in enumerate(test_strings):
        try:
            coords = parser.parse_coordinate_string(coord_str)
            geom_type = parser.detect_geometry_type(coords)
            geometry = parser.create_geometry(coords)
            print(f"测试 {i+1}: {geom_type} - {geometry}")
        except Exception as e:
            print(f"测试 {i+1} 失败: {e}")

    # 测试DataFrame解析
    test_data = pd.DataFrame({
        'name': ['点1', '线1', '面1'],
        'coordinates': test_strings
    })

    print("\nDataFrame测试:")
    for geom_type in ['auto', 'Point', 'LineString', 'Polygon']:
        try:
            geometries = parser.parse_dataframe_column(test_data, 'coordinates', geom_type)
            print(f"几何类型 {geom_type}: 成功创建 {len([g for g in geometries if g is not None])} 个对象")
        except Exception as e:
            print(f"几何类型 {geom_type}: 失败 - {e}")