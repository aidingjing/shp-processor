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
        # 经纬度字段匹配模式
        self.lng_patterns = [
            r'lng', r'lon', r'longitude', r'经度', r'x', r'coord_x',
            r'longitude_dec', r'lng_dec', r'long'
        ]
        self.lat_patterns = [
            r'lat', r'latitude', r'纬度', r'y', r'coord_y',
            r'latitude_dec', r'lat_dec'
        ]

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

    def detect_coordinate_columns(self, df: pd.DataFrame, debug: bool = False) -> dict:
        """
        自动检测DataFrame中的经纬度字段

        Args:
            df: 要分析的DataFrame
            debug: 是否输出调试信息

        Returns:
            dict: 检测结果，包含经度字段、纬度字段和置信度
        """
        result = {
            "lng_columns": [],
            "lat_columns": [],
            "pair_suggestions": [],
            "confidence": 0.0
        }

        if debug:
            print("DEBUG: 开始检测经纬度字段")
            print(f"DEBUG: 共有 {len(df.columns)} 个字段")

        # 检测数值型字段
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

        if debug:
            print(f"DEBUG: 数值型字段: {numeric_columns}")

        # 检测经度字段
        for col in numeric_columns:
            col_lower = col.lower()
            for pattern in self.lng_patterns:
                if re.search(pattern, col_lower, re.IGNORECASE):
                    result["lng_columns"].append(col)
                    if debug:
                        print(f"DEBUG: 检测到可能的经度字段: {col} (匹配模式: {pattern})")
                    break

        # 检测纬度字段
        for col in numeric_columns:
            col_lower = col.lower()
            for pattern in self.lat_patterns:
                if re.search(pattern, col_lower, re.IGNORECASE):
                    result["lat_columns"].append(col)
                    if debug:
                        print(f"DEBUG: 检测到可能的纬度字段: {col} (匹配模式: {pattern})")
                    break

        # 生成配对建议
        for lng_col in result["lng_columns"]:
            for lat_col in result["lat_columns"]:
                # 检查数据范围是否合理
                lng_sample = df[lng_col].dropna().head(100)
                lat_sample = df[lat_col].dropna().head(100)

                if len(lng_sample) > 0 and len(lat_sample) > 0:
                    lng_mean = lng_sample.mean()
                    lat_mean = lat_sample.mean()

                    # 经度范围检查 (-180 到 180)
                    # 纬度范围检查 (-90 到 90)
                    if (-180 <= lng_mean <= 180) and (-90 <= lat_mean <= 90):
                        confidence = min(len(lng_sample), len(lat_sample)) / 100.0
                        result["pair_suggestions"].append({
                            "lng_column": lng_col,
                            "lat_column": lat_col,
                            "confidence": confidence,
                            "lng_mean": lng_mean,
                            "lat_mean": lat_mean
                        })

        # 计算总体置信度
        if result["pair_suggestions"]:
            result["confidence"] = max([pair["confidence"] for pair in result["pair_suggestions"]])

        if debug:
            print(f"DEBUG: 检测到 {len(result['lng_columns'])} 个经度字段")
            print(f"DEBUG: 检测到 {len(result['lat_columns'])} 个纬度字段")
            print(f"DEBUG: 生成 {len(result['pair_suggestions'])} 个配对建议")
            print(f"DEBUG: 总体置信度: {result['confidence']}")

        return result

    def parse_separate_coordinates(self, df: pd.DataFrame, lng_column: str, lat_column: str,
                                 geometry_type: str = "Point") -> List[Union[Point, LineString, Polygon]]:
        """
        从分离的经纬度字段解析坐标

        Args:
            df: 包含经纬度数据的DataFrame
            lng_column: 经度字段名
            lat_column: 纬度字段名
            geometry_type: 几何类型，默认为Point

        Returns:
            List[Union[Point, LineString, Polygon]]: 几何对象列表
        """
        if lng_column not in df.columns:
            raise ValueError(f"经度字段 '{lng_column}' 不存在")
        if lat_column not in df.columns:
            raise ValueError(f"纬度字段 '{lat_column}' 不存在")

        geometries = []
        failed_count = 0

        for idx, (lng, lat) in enumerate(zip(df[lng_column], df[lat_column])):
            try:
                # 检查空值
                if (lng is None or lat is None or
                    (isinstance(lng, float) and pd.isna(lng)) or
                    (isinstance(lat, float) and pd.isna(lat))):
                    geometries.append(None)
                    continue

                # 转换为float
                lng_float = float(lng)
                lat_float = float(lat)

                # 验证坐标范围
                if not (-180 <= lng_float <= 180):
                    print(f"警告: 第 {idx + 1} 行经度超出范围: {lng_float}")
                    geometries.append(None)
                    continue

                if not (-90 <= lat_float <= 90):
                    print(f"警告: 第 {idx + 1} 行纬度超出范围: {lat_float}")
                    geometries.append(None)
                    continue

                # 创建几何对象
                if geometry_type == "Point":
                    geometries.append(Point(lng_float, lat_float))
                else:
                    # 对于其他几何类型，需要将单个点转换为坐标列表
                    coords = [(lng_float, lat_float)]
                    geometry = self.create_geometry(coords, geometry_type)
                    geometries.append(geometry)

            except Exception as e:
                print(f"解析第 {idx + 1} 行坐标失败: {e}")
                geometries.append(None)
                failed_count += 1

        if failed_count > 0:
            print(f"警告: 共有 {failed_count} 个坐标点解析失败")

        return geometries

    def analyze_separate_coordinates(self, df: pd.DataFrame, lng_column: str, lat_column: str,
                                   sample_size: int = 100, debug: bool = False) -> dict:
        """
        分析分离的经纬度字段的数据质量

        Args:
            df: 包含经纬度数据的DataFrame
            lng_column: 经度字段名
            lat_column: 纬度字段名
            sample_size: 采样大小
            debug: 是否输出调试信息

        Returns:
            dict: 分析结果
        """
        if lng_column not in df.columns:
            raise ValueError(f"经度字段 '{lng_column}' 不存在")
        if lat_column not in df.columns:
            raise ValueError(f"纬度字段 '{lat_column}' 不存在")

        # 采样数据
        lng_sample = df[lng_column].dropna().head(sample_size)
        lat_sample = df[lat_column].dropna().head(sample_size)

        # 统计信息
        total_records = len(df)
        valid_lng = len(lng_sample)
        valid_lat = len(lat_sample)
        valid_pairs = min(valid_lng, valid_lat)

        # 数据范围分析
        lng_min, lng_max = lng_sample.min(), lng_sample.max()
        lat_min, lat_max = lat_sample.min(), lat_sample.max()
        lng_mean = lng_sample.mean()
        lat_mean = lat_sample.mean()

        # 数据质量检查
        out_of_range_lng = ((lng_sample < -180) | (lng_sample > 180)).sum()
        out_of_range_lat = ((lat_sample < -90) | (lat_sample > 90)).sum()

        # 置信度计算
        completeness = valid_pairs / total_records if total_records > 0 else 0
        range_validity = 1 - ((out_of_range_lng + out_of_range_lat) / valid_pairs) if valid_pairs > 0 else 0
        confidence = completeness * range_validity

        result = {
            "total_records": total_records,
            "valid_coordinates": valid_pairs,
            "completeness": completeness,
            "lng_stats": {
                "min": lng_min,
                "max": lng_max,
                "mean": lng_mean,
                "out_of_range_count": out_of_range_lng
            },
            "lat_stats": {
                "min": lat_min,
                "max": lat_max,
                "mean": lat_mean,
                "out_of_range_count": out_of_range_lat
            },
            "range_validity": range_validity,
            "confidence": confidence,
            "suggested_geometry": "Point"
        }

        if debug:
            print(f"DEBUG: 分析分离坐标字段 '{lng_column}' 和 '{lat_column}'")
            print(f"DEBUG: 总记录数: {total_records}")
            print(f"DEBUG: 有效坐标对: {valid_pairs}")
            print(f"DEBUG: 完整性: {completeness:.2%}")
            print(f"DEBUG: 范围有效性: {range_validity:.2%}")
            print(f"DEBUG: 置信度: {confidence:.2%}")
            print(f"DEBUG: 经度范围: [{lng_min:.6f}, {lng_max:.6f}]")
            print(f"DEBUG: 纬度范围: [{lat_min:.6f}, {lat_max:.6f}]")

        return result


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

    # 测试分离的经纬度字段
    print("\n=== 测试分离的经纬度字段功能 ===")

    # 创建测试数据
    separate_test_data = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'name': ['地点A', '地点B', '地点C', '地点D'],
        'longitude': [116.404, 116.405, 116.406, 116.407],
        'latitude': [39.915, 39.916, 39.917, 39.918],
        'lng': [116.408, 116.409, 116.410, 116.411],
        'lat': [39.919, 39.920, 39.921, 39.922],
        'description': ['测试点1', '测试点2', '测试点3', '测试点4']
    })

    print("测试数据:")
    print(separate_test_data)

    # 测试字段检测
    print("\n字段检测测试:")
    detection_result = parser.detect_coordinate_columns(separate_test_data, debug=True)
    print(f"检测到的经度字段: {detection_result['lng_columns']}")
    print(f"检测到的纬度字段: {detection_result['lat_columns']}")
    print(f"配对建议: {detection_result['pair_suggestions']}")
    print(f"总体置信度: {detection_result['confidence']}")

    # 测试分离坐标解析
    if detection_result['pair_suggestions']:
        best_pair = detection_result['pair_suggestions'][0]
        lng_col = best_pair['lng_column']
        lat_col = best_pair['lat_column']

        print(f"\n使用最佳配对: {lng_col} + {lat_col}")
        geometries = parser.parse_separate_coordinates(separate_test_data, lng_col, lat_col)
        valid_geometries = [g for g in geometries if g is not None]
        print(f"成功创建 {len(valid_geometries)} 个几何对象")

        # 分析数据质量
        analysis = parser.analyze_separate_coordinates(separate_test_data, lng_col, lat_col, debug=True)
        print(f"数据质量分析: 完整性 {analysis['completeness']:.2%}, 置信度 {analysis['confidence']:.2%}")

    print("\n=== 功能测试完成 ===")