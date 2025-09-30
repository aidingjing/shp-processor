"""
SHP文件导出器模块
将包含坐标数据的DataFrame导出为SHP文件
"""

import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from core.coordinate_parser import CoordinateParser


class ShapefileExporter:
    """SHP文件导出器"""

    # 常用的坐标系定义
    COMMON_CRS = {
        "WGS84": "EPSG:4326",
        "GCJ02": "EPSG:4490",  # 中国测绘坐标系
        "BD09": "EPSG:4326",   # 百度坐标系（使用WGS84代码）
        "Web Mercator": "EPSG:3857",
        "UTM Zone 49N": "EPSG:32649",  # 北京地区UTM
        "UTM Zone 50N": "EPSG:32650",  # 上海地区UTM
    }

    def __init__(self):
        """初始化导出器"""
        self.coordinate_parser = CoordinateParser()

    def export_to_shapefile(self,
                          df: pd.DataFrame,
                          coordinate_column: str,
                          output_path: str,
                          geometry_type: str = "auto",
                          crs: str = "WGS84",
                          encoding: str = "utf-8") -> bool:
        """
        将DataFrame导出为SHP文件

        Args:
            df: 包含坐标数据的DataFrame
            coordinate_column: 坐标列名
            output_path: 输出文件路径
            geometry_type: 几何类型 (auto/Point/LineString/Polygon)
            crs: 坐标系名称或EPSG代码
            encoding: 文件编码

        Returns:
            bool: 导出是否成功
        """
        try:
            # 验证输入参数
            if df.empty:
                raise ValueError("DataFrame为空")
            if coordinate_column not in df.columns:
                raise ValueError(f"列 '{coordinate_column}' 不存在")

            # 解析坐标数据
            geometries = self.coordinate_parser.parse_dataframe_column(
                df, coordinate_column, geometry_type
            )

            # 创建GeoDataFrame
            gdf = self._create_geodataframe(df, geometries, coordinate_column)

            # 设置坐标系
            crs_code = self._get_crs_code(crs)
            gdf = gdf.set_crs(crs_code, allow_override=True)

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 导出SHP文件
            gdf.to_file(output_path, encoding=encoding, driver='ESRI Shapefile')

            print(f"成功导出SHP文件: {output_path}")
            print(f"几何对象数量: {len(gdf)}")
            print(f"坐标系: {crs_code}")
            print(f"字段数量: {len(gdf.columns) - 1}")  # 减去geometry列

            return True

        except Exception as e:
            print(f"导出SHP文件失败: {e}")
            return False

    def _create_geodataframe(self, df: pd.DataFrame, geometries: List, coordinate_column: str) -> gpd.GeoDataFrame:
        """
        创建GeoDataFrame

        Args:
            df: 原始DataFrame
            geometries: 几何对象列表
            coordinate_column: 坐标列名

        Returns:
            gpd.GeoDataFrame: 创建的GeoDataFrame
        """
        # 创建副本避免修改原始数据
        df_copy = df.copy()

        # 移除坐标列（因为我们已经解析为几何对象）
        if coordinate_column in df_copy.columns:
            df_copy = df_copy.drop(columns=[coordinate_column])

        # 过滤掉无效的几何对象
        valid_indices = [i for i, geom in enumerate(geometries) if geom is not None]
        valid_geometries = [geometries[i] for i in valid_indices]
        valid_data = df_copy.iloc[valid_indices].copy()

        if len(valid_geometries) == 0:
            raise ValueError("没有有效的几何对象可供导出")

        # 创建GeoDataFrame
        gdf = gpd.GeoDataFrame(valid_data, geometry=valid_geometries)

        print(f"有效几何对象: {len(valid_geometries)}")
        print(f"无效记录: {len(geometries) - len(valid_geometries)}")

        return gdf

    def _get_crs_code(self, crs: str) -> str:
        """
        获取CRS代码

        Args:
            crs: 坐标系名称或EPSG代码

        Returns:
            str: CRS代码
        """
        # 如果是EPSG代码，直接返回
        if crs.upper().startswith("EPSG:"):
            return crs.upper()

        # 查找预定义的坐标系
        for name, code in self.COMMON_CRS.items():
            if crs.lower() == name.lower():
                return code

        # 尝试作为EPSG代码解析
        try:
            epsg_code = int(crs)
            return f"EPSG:{epsg_code}"
        except ValueError:
            pass

        # 默认返回WGS84
        print(f"未识别的坐标系 '{crs}'，使用默认的WGS84坐标系")
        return "EPSG:4326"

    def preview_export(self,
                      df: pd.DataFrame,
                      coordinate_column: str,
                      geometry_type: str = "auto") -> Dict[str, Any]:
        """
        预览导出结果

        Args:
            df: 包含坐标数据的DataFrame
            coordinate_column: 坐标列名
            geometry_type: 几何类型

        Returns:
            Dict: 预览信息
        """
        try:
            # 解析坐标数据
            geometries = self.coordinate_parser.parse_dataframe_column(
                df, coordinate_column, geometry_type
            )

            # 统计几何类型
            geom_types = {}
            for geom in geometries:
                if geom is not None:
                    geom_type = type(geom).__name__
                    geom_types[geom_type] = geom_types.get(geom_type, 0) + 1

            # 计算有效记录数
            valid_count = sum(1 for geom in geometries if geom is not None)
            total_count = len(geometries)

            # 分析数据
            preview_info = {
                "total_records": total_count,
                "valid_records": valid_count,
                "invalid_records": total_count - valid_count,
                "success_rate": valid_count / total_count if total_count > 0 else 0,
                "geometry_types": geom_types,
                "columns": [col for col in df.columns if col != coordinate_column],
                "coordinate_column": coordinate_column
            }

            return preview_info

        except Exception as e:
            return {"error": str(e)}

    def get_supported_geometry_types(self) -> List[str]:
        """
        获取支持的几何类型

        Returns:
            List[str]: 支持的几何类型列表
        """
        return ["auto", "Point", "LineString", "Polygon"]

    def get_supported_crs(self) -> Dict[str, str]:
        """
        获取支持的坐标系

        Returns:
            Dict[str, str]: 坐标系名称到代码的映射
        """
        return self.COMMON_CRS.copy()

    def convert_crs(self,
                   input_path: str,
                   output_path: str,
                   target_crs: str,
                   encoding: str = "utf-8") -> bool:
        """
        转换SHP文件的坐标系

        Args:
            input_path: 输入SHP文件路径
            output_path: 输出SHP文件路径
            target_crs: 目标坐标系
            encoding: 文件编码

        Returns:
            bool: 转换是否成功
        """
        try:
            # 读取SHP文件
            gdf = gpd.read_file(input_path, encoding=encoding)

            # 获取目标CRS代码
            target_crs_code = self._get_crs_code(target_crs)

            # 转换坐标系
            gdf_transformed = gdf.to_crs(target_crs_code)

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 保存转换后的文件
            gdf_transformed.to_file(output_path, encoding=encoding, driver='ESRI Shapefile')

            print(f"坐标系转换成功: {input_path} -> {output_path}")
            print(f"原坐标系: {gdf.crs}")
            print(f"目标坐标系: {target_crs_code}")

            return True

        except Exception as e:
            print(f"坐标系转换失败: {e}")
            return False

    def validate_output_path(self, output_path: str) -> tuple[bool, str]:
        """
        验证输出路径

        Args:
            output_path: 输出路径

        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not output_path:
            return False, "输出路径不能为空"

        # 检查文件扩展名
        if not output_path.lower().endswith('.shp'):
            return False, "输出文件必须以.shp结尾"

        # 检查目录是否可写
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                return False, f"无法创建输出目录: {e}"
        elif output_dir:
            if not os.access(output_dir, os.W_OK):
                return False, "输出目录没有写入权限"

        return True, "路径有效"


if __name__ == "__main__":
    # 测试代码
    exporter = ShapefileExporter()

    # 创建测试数据
    test_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['点1', '线1', '面1'],
        'coordinates': [
            "[[116.404, 39.915]]",
            "[[116.404, 39.915], [116.405, 39.916]]",
            "[[116.404, 39.915], [116.405, 39.916], [116.406, 39.917], [116.404, 39.915]]"
        ]
    })

    # 预览导出结果
    preview = exporter.preview_export(test_data, 'coordinates')
    print("预览信息:", preview)

    # 测试导出
    output_path = "test_output.shp"
    success = exporter.export_to_shapefile(
        test_data,
        'coordinates',
        output_path,
        geometry_type="auto",
        crs="WGS84"
    )

    if success:
        print(f"测试导出成功: {output_path}")
    else:
        print("测试导出失败")