#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空间统计分析模块
提供空间关系分析和统计功能

作者: Claude Code
创建时间: 2024-10-09
"""

import logging
import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple, Optional, Union, Any
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from shapely.ops import unary_union
from rtree import index
import warnings

# 忽略一些警告信息
warnings.filterwarnings('ignore', category=UserWarning)


class SpatialAnalyzer:
    """空间统计分析器"""

    def __init__(self):
        """初始化分析器"""
        self.logger = logging.getLogger(__name__)
        self.polygons_gdf: Optional[gpd.GeoDataFrame] = None
        self.target_gdf: Optional[gpd.GeoDataFrame] = None
        self.spatial_index: Optional[index.Index] = None

    def load_polygons_layer(self, file_path: str, id_field: str = None) -> Dict[str, Any]:
        """
        加载面图层

        Args:
            file_path: SHP文件路径
            id_field: 唯一标识字段名

        Returns:
            Dict: 加载结果
        """
        try:
            # 读取SHP文件
            gdf = gpd.read_file(file_path)

            # 验证是否包含面几何类型
            valid_geom_types = ['Polygon', 'MultiPolygon']
            if not any(geom_type in gdf.geometry.geom_type.unique() for geom_type in valid_geom_types):
                return {
                    'success': False,
                    'error': '文件不包含面几何类型，请选择包含Polygon或MultiPolygon的SHP文件'
                }

            # 过滤出面要素
            polygons_mask = gdf.geometry.geom_type.isin(valid_geom_types)
            self.polygons_gdf = gdf[polygons_mask].copy()

            if self.polygons_gdf.empty:
                return {
                    'success': False,
                    'error': '文件中没有有效的面要素'
                }

            # 设置唯一标识字段
            if id_field and id_field in self.polygons_gdf.columns:
                self.polygons_gdf['_analysis_id'] = self.polygons_gdf[id_field]
            else:
                self.polygons_gdf['_analysis_id'] = range(len(self.polygons_gdf))

            # 创建空间索引
            self._create_spatial_index()

            return {
                'success': True,
                'polygon_count': len(self.polygons_gdf),
                'columns': list(self.polygons_gdf.columns),
                'bounds': self.polygons_gdf.total_bounds.tolist()
            }

        except Exception as e:
            self.logger.error(f"加载面图层失败: {e}")
            return {
                'success': False,
                'error': f'加载面图层失败: {str(e)}'
            }

    def load_target_layer(self, file_path: str, id_field: str = None) -> Dict[str, Any]:
        """
        加载目标图层（点、线、面）

        Args:
            file_path: SHP文件路径
            id_field: 唯一标识字段名

        Returns:
            Dict: 加载结果
        """
        try:
            # 读取SHP文件
            gdf = gpd.read_file(file_path)

            if gdf.empty:
                return {
                    'success': False,
                    'error': '文件为空'
                }

            self.target_gdf = gdf.copy()

            # 设置唯一标识字段
            if id_field and id_field in self.target_gdf.columns:
                self.target_gdf['_target_id'] = self.target_gdf[id_field]
            else:
                self.target_gdf['_target_id'] = range(len(self.target_gdf))

            # 获取几何类型信息
            geom_types = gdf.geometry.geom_type.value_counts().to_dict()

            return {
                'success': True,
                'feature_count': len(self.target_gdf),
                'geometry_types': geom_types,
                'columns': list(self.target_gdf.columns),
                'bounds': self.target_gdf.total_bounds.tolist()
            }

        except Exception as e:
            self.logger.error(f"加载目标图层失败: {e}")
            return {
                'success': False,
                'error': f'加载目标图层失败: {str(e)}'
            }

    def _create_spatial_index(self):
        """创建空间索引"""
        if self.polygons_gdf is not None:
            self.spatial_index = index.Index()
            for idx, geometry in enumerate(self.polygons_gdf.geometry):
                self.spatial_index.insert(idx, geometry.bounds)

    def analyze_points_in_polygons(self) -> Dict[str, Any]:
        """
        分析点在面内的分布

        Returns:
            Dict: 分析结果
        """
        if self.polygons_gdf is None or self.target_gdf is None:
            return {
                'success': False,
                'error': '请先加载面图层和目标图层'
            }

        try:
            # 过滤出点要素
            points_mask = self.target_gdf.geometry.geom_type.isin(['Point', 'MultiPoint'])
            points_gdf = self.target_gdf[points_mask].copy()

            if points_gdf.empty:
                return {
                    'success': False,
                    'error': '目标图层中没有点要素'
                }

            # 统计结果
            statistics = {}
            unassigned_points = []

            # 为每个点找到包含它的面
            for point_idx, point_row in points_gdf.iterrows():
                point_geom = point_row.geometry
                point_id = point_row['_target_id']

                # 处理多点情况
                if isinstance(point_geom, MultiPoint):
                    points = list(point_geom.geoms)
                else:
                    points = [point_geom]

                assigned_polygons = set()

                for point in points:
                    # 使用空间索引快速筛选可能包含该点的面
                    possible_matches = list(self.spatial_index.intersection(point.bounds))

                    for polygon_idx in possible_matches:
                        polygon_geom = self.polygons_gdf.iloc[polygon_idx].geometry
                        polygon_id = self.polygons_gdf.iloc[polygon_idx]['_analysis_id']

                        # 检查点是否在面内
                        if polygon_geom.contains(point) or polygon_geom.touches(point):
                            assigned_polygons.add(polygon_id)

                # 记录统计结果
                if assigned_polygons:
                    for polygon_id in assigned_polygons:
                        if polygon_id not in statistics:
                            statistics[polygon_id] = {
                                'polygon_id': polygon_id,
                                'point_count': 0,
                                'point_ids': []
                            }
                        statistics[polygon_id]['point_count'] += 1
                        statistics[polygon_id]['point_ids'].append(point_id)
                else:
                    unassigned_points.append(point_id)

            # 创建结果DataFrame
            result_data = []
            for polygon_id, stats in statistics.items():
                result_data.append({
                    'polygon_id': polygon_id,
                    'point_count': stats['point_count'],
                    'point_ids': stats['point_ids']
                })

            result_df = pd.DataFrame(result_data)

            # 添加没有点的面（计数为0）
            all_polygon_ids = set(self.polygons_gdf['_analysis_id'])
            assigned_polygon_ids = set(statistics.keys())
            empty_polygon_ids = all_polygon_ids - assigned_polygon_ids

            for polygon_id in empty_polygon_ids:
                result_df = pd.concat([result_df, pd.DataFrame([{
                    'polygon_id': polygon_id,
                    'point_count': 0,
                    'point_ids': []
                }])], ignore_index=True)

            return {
                'success': True,
                'analysis_type': 'points_in_polygons',
                'total_points': len(points_gdf),
                'assigned_points': len(points_gdf) - len(unassigned_points),
                'unassigned_points': len(unassigned_points),
                'unassigned_point_ids': unassigned_points,
                'statistics': result_df,
                'summary': {
                    'total_polygons': len(self.polygons_gdf),
                    'polygons_with_points': len(statistics),
                    'max_points_per_polygon': result_df['point_count'].max() if not result_df.empty else 0,
                    'avg_points_per_polygon': result_df['point_count'].mean() if not result_df.empty else 0
                }
            }

        except Exception as e:
            self.logger.error(f"点面分析失败: {e}")
            return {
                'success': False,
                'error': f'点面分析失败: {str(e)}'
            }

    def analyze_lines_in_polygons(self) -> Dict[str, Any]:
        """
        分析线在面内的分布（按落入比例最多的面统计）

        Returns:
            Dict: 分析结果
        """
        if self.polygons_gdf is None or self.target_gdf is None:
            return {
                'success': False,
                'error': '请先加载面图层和目标图层'
            }

        try:
            # 过滤出线要素
            lines_mask = self.target_gdf.geometry.geom_type.isin(['LineString', 'MultiLineString'])
            lines_gdf = self.target_gdf[lines_mask].copy()

            if lines_gdf.empty:
                return {
                    'success': False,
                    'error': '目标图层中没有线要素'
                }

            # 统计结果
            statistics = {}
            unassigned_lines = []

            # 为每条线找到最佳匹配的面
            for line_idx, line_row in lines_gdf.iterrows():
                line_geom = line_row.geometry
                line_id = line_row['_target_id']

                # 处理多线情况
                if isinstance(line_geom, MultiLineString):
                    lines = list(line_geom.geoms)
                else:
                    lines = [line_geom]

                best_match = None
                best_ratio = 0.0

                for line in lines:
                    # 使用空间索引快速筛选可能相交的面
                    possible_matches = list(self.spatial_index.intersection(line.bounds))

                    for polygon_idx in possible_matches:
                        polygon_geom = self.polygons_gdf.iloc[polygon_idx].geometry
                        polygon_id = self.polygons_gdf.iloc[polygon_idx]['_analysis_id']

                        # 计算线与面的交集
                        intersection = line.intersection(polygon_geom)

                        if not intersection.is_empty:
                            # 计算落入比例
                            if hasattr(intersection, 'length') and intersection.length > 0:
                                ratio = intersection.length / line.length
                            else:
                                # 如果交集长度为0，检查是否完全包含
                                if polygon_geom.contains(line):
                                    ratio = 1.0
                                else:
                                    ratio = 0.0

                            if ratio > best_ratio:
                                best_ratio = ratio
                                best_match = polygon_id

                # 记录统计结果
                if best_match is not None and best_ratio > 0:
                    if best_match not in statistics:
                        statistics[best_match] = {
                            'polygon_id': best_match,
                            'line_count': 0,
                            'line_ids': [],
                            'total_length': 0.0,
                            'intersection_ratio_sum': 0.0
                        }

                    statistics[best_match]['line_count'] += 1
                    statistics[best_match]['line_ids'].append(line_id)
                    statistics[best_match]['total_length'] += line.length
                    statistics[best_match]['intersection_ratio_sum'] += best_ratio
                else:
                    unassigned_lines.append(line_id)

            # 创建结果DataFrame
            result_data = []
            for polygon_id, stats in statistics.items():
                result_data.append({
                    'polygon_id': polygon_id,
                    'line_count': stats['line_count'],
                    'line_ids': stats['line_ids'],
                    'total_length': stats['total_length'],
                    'avg_intersection_ratio': stats['intersection_ratio_sum'] / stats['line_count']
                })

            result_df = pd.DataFrame(result_data)

            # 添加没有线的面（计数为0）
            all_polygon_ids = set(self.polygons_gdf['_analysis_id'])
            assigned_polygon_ids = set(statistics.keys())
            empty_polygon_ids = all_polygon_ids - assigned_polygon_ids

            for polygon_id in empty_polygon_ids:
                result_df = pd.concat([result_df, pd.DataFrame([{
                    'polygon_id': polygon_id,
                    'line_count': 0,
                    'line_ids': [],
                    'total_length': 0.0,
                    'avg_intersection_ratio': 0.0
                }])], ignore_index=True)

            return {
                'success': True,
                'analysis_type': 'lines_in_polygons',
                'total_lines': len(lines_gdf),
                'assigned_lines': len(lines_gdf) - len(unassigned_lines),
                'unassigned_lines': len(unassigned_lines),
                'unassigned_line_ids': unassigned_lines,
                'statistics': result_df,
                'summary': {
                    'total_polygons': len(self.polygons_gdf),
                    'polygons_with_lines': len(statistics),
                    'max_lines_per_polygon': result_df['line_count'].max() if not result_df.empty else 0,
                    'avg_lines_per_polygon': result_df['line_count'].mean() if not result_df.empty else 0
                }
            }

        except Exception as e:
            self.logger.error(f"线面分析失败: {e}")
            return {
                'success': False,
                'error': f'线面分析失败: {str(e)}'
            }

    def analyze_polygons_in_polygons(self) -> Dict[str, Any]:
        """
        分析面与面的重叠关系（按重叠面积最大的面统计）

        Returns:
            Dict: 分析结果
        """
        if self.polygons_gdf is None or self.target_gdf is None:
            return {
                'success': False,
                'error': '请先加载面图层和目标图层'
            }

        try:
            # 过滤出面要素
            polygons_mask = self.target_gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])
            target_polygons_gdf = self.target_gdf[polygons_mask].copy()

            if target_polygons_gdf.empty:
                return {
                    'success': False,
                    'error': '目标图层中没有面要素'
                }

            # 统计结果
            statistics = {}
            unassigned_polygons = []

            # 为每个目标面找到最佳匹配的分析面
            for target_idx, target_row in target_polygons_gdf.iterrows():
                target_geom = target_row.geometry
                target_id = target_row['_target_id']

                # 处理多面情况
                if isinstance(target_geom, MultiPolygon):
                    target_polys = list(target_geom.geoms)
                else:
                    target_polys = [target_geom]

                best_match = None
                best_overlap_ratio = 0.0

                for target_poly in target_polys:
                    # 使用空间索引快速筛选可能相交的面
                    possible_matches = list(self.spatial_index.intersection(target_poly.bounds))

                    for polygon_idx in possible_matches:
                        polygon_geom = self.polygons_gdf.iloc[polygon_idx].geometry
                        polygon_id = self.polygons_gdf.iloc[polygon_idx]['_analysis_id']

                        # 计算面与面的交集
                        intersection = target_poly.intersection(polygon_geom)

                        if not intersection.is_empty and hasattr(intersection, 'area'):
                            # 计算重叠比例
                            overlap_ratio = intersection.area / target_poly.area

                            if overlap_ratio > best_overlap_ratio:
                                best_overlap_ratio = overlap_ratio
                                best_match = polygon_id

                # 记录统计结果
                if best_match is not None and best_overlap_ratio > 0:
                    if best_match not in statistics:
                        statistics[best_match] = {
                            'polygon_id': best_match,
                            'target_polygon_count': 0,
                            'target_polygon_ids': [],
                            'total_target_area': 0.0,
                            'total_overlap_area': 0.0,
                            'avg_overlap_ratio': 0.0
                        }

                    statistics[best_match]['target_polygon_count'] += 1
                    statistics[best_match]['target_polygon_ids'].append(target_id)
                    statistics[best_match]['total_target_area'] += target_poly.area
                    statistics[best_match]['total_overlap_area'] += target_poly.area * best_overlap_ratio
                else:
                    unassigned_polygons.append(target_id)

            # 计算平均重叠比例
            for polygon_id in statistics:
                stats = statistics[polygon_id]
                if stats['target_polygon_count'] > 0:
                    stats['avg_overlap_ratio'] = stats['total_overlap_area'] / stats['total_target_area']

            # 创建结果DataFrame
            result_data = []
            for polygon_id, stats in statistics.items():
                result_data.append({
                    'polygon_id': polygon_id,
                    'target_polygon_count': stats['target_polygon_count'],
                    'target_polygon_ids': stats['target_polygon_ids'],
                    'total_target_area': stats['total_target_area'],
                    'total_overlap_area': stats['total_overlap_area'],
                    'avg_overlap_ratio': stats['avg_overlap_ratio']
                })

            result_df = pd.DataFrame(result_data)

            # 添加没有目标面的面（计数为0）
            all_polygon_ids = set(self.polygons_gdf['_analysis_id'])
            assigned_polygon_ids = set(statistics.keys())
            empty_polygon_ids = all_polygon_ids - assigned_polygon_ids

            for polygon_id in empty_polygon_ids:
                result_df = pd.concat([result_df, pd.DataFrame([{
                    'polygon_id': polygon_id,
                    'target_polygon_count': 0,
                    'target_polygon_ids': [],
                    'total_target_area': 0.0,
                    'total_overlap_area': 0.0,
                    'avg_overlap_ratio': 0.0
                }])], ignore_index=True)

            return {
                'success': True,
                'analysis_type': 'polygons_in_polygons',
                'total_target_polygons': len(target_polygons_gdf),
                'assigned_polygons': len(target_polygons_gdf) - len(unassigned_polygons),
                'unassigned_polygons': len(unassigned_polygons),
                'unassigned_polygon_ids': unassigned_polygons,
                'statistics': result_df,
                'summary': {
                    'total_polygons': len(self.polygons_gdf),
                    'polygons_with_targets': len(statistics),
                    'max_targets_per_polygon': result_df['target_polygon_count'].max() if not result_df.empty else 0,
                    'avg_targets_per_polygon': result_df['target_polygon_count'].mean() if not result_df.empty else 0
                }
            }

        except Exception as e:
            self.logger.error(f"面面分析失败: {e}")
            return {
                'success': False,
                'error': f'面面分析失败: {str(e)}'
            }

    def perform_spatial_analysis(self) -> Dict[str, Any]:
        """
        执行完整的空间统计分析

        Returns:
            Dict: 分析结果
        """
        if self.polygons_gdf is None or self.target_gdf is None:
            return {
                'success': False,
                'error': '请先加载面图层和目标图层'
            }

        # 确定目标图层的几何类型
        geom_types = self.target_gdf.geometry.geom_type.unique()

        results = {}

        # 根据几何类型执行相应的分析
        if any(geom_type in geom_types for geom_type in ['Point', 'MultiPoint']):
            point_result = self.analyze_points_in_polygons()
            if point_result['success']:
                results['points'] = point_result

        if any(geom_type in geom_types for geom_type in ['LineString', 'MultiLineString']):
            line_result = self.analyze_lines_in_polygons()
            if line_result['success']:
                results['lines'] = line_result

        if any(geom_type in geom_types for geom_type in ['Polygon', 'MultiPolygon']):
            polygon_result = self.analyze_polygons_in_polygons()
            if polygon_result['success']:
                results['polygons'] = polygon_result

        if not results:
            return {
                'success': False,
                'error': '无法识别目标图层的几何类型'
            }

        # 生成总体摘要
        total_summary = {
            'analysis_types': list(results.keys()),
            'polygon_layer_info': {
                'total_polygons': len(self.polygons_gdf),
                'bounds': self.polygons_gdf.total_bounds.tolist()
            },
            'target_layer_info': {
                'total_features': len(self.target_gdf),
                'geometry_types': self.target_gdf.geometry.geom_type.value_counts().to_dict(),
                'bounds': self.target_gdf.total_bounds.tolist()
            }
        }

        return {
            'success': True,
            'results': results,
            'summary': total_summary
        }

    def export_results_to_shapefile(self, results: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """
        将分析结果导出为SHP文件

        Args:
            results: 分析结果
            output_path: 输出文件路径

        Returns:
            Dict: 导出结果
        """
        try:
            if not results.get('success', False):
                return {
                    'success': False,
                    'error': '无效的分析结果'
                }

            # 复制面图层
            result_gdf = self.polygons_gdf.copy()

            # 为每种分析类型添加统计字段
            analysis_data = results.get('results', {})

            # 点统计字段
            if 'points' in analysis_data:
                points_stats = analysis_data['points']['statistics']
                points_dict = dict(zip(points_stats['polygon_id'], points_stats['point_count']))
                result_gdf['point_count'] = result_gdf['_analysis_id'].map(points_dict).fillna(0)
            else:
                result_gdf['point_count'] = 0

            # 线统计字段
            if 'lines' in analysis_data:
                lines_stats = analysis_data['lines']['statistics']
                lines_dict = dict(zip(lines_stats['polygon_id'], lines_stats['line_count']))
                result_gdf['line_count'] = result_gdf['_analysis_id'].map(lines_dict).fillna(0)
            else:
                result_gdf['line_count'] = 0

            # 面统计字段
            if 'polygons' in analysis_data:
                polygons_stats = analysis_data['polygons']['statistics']
                polygons_dict = dict(zip(polygons_stats['polygon_id'], polygons_stats['target_polygon_count']))
                result_gdf['polygon_count'] = result_gdf['_analysis_id'].map(polygons_dict).fillna(0)
            else:
                result_gdf['polygon_count'] = 0

            # 添加总计数字段
            result_gdf['total_count'] = result_gdf['point_count'] + result_gdf['line_count'] + result_gdf['polygon_count']

            # 导出SHP文件
            result_gdf.to_file(output_path, encoding='utf-8')

            return {
                'success': True,
                'output_path': output_path,
                'exported_features': len(result_gdf),
                'fields': ['point_count', 'line_count', 'polygon_count', 'total_count']
            }

        except Exception as e:
            self.logger.error(f"导出SHP文件失败: {e}")
            return {
                'success': False,
                'error': f'导出SHP文件失败: {str(e)}'
            }

    def export_results_to_excel(self, results: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """
        将分析结果导出为Excel文件

        Args:
            results: 分析结果
            output_path: 输出文件路径

        Returns:
            Dict: 导出结果
        """
        try:
            import openpyxl

            if not results.get('success', False):
                return {
                    'success': False,
                    'error': '无效的分析结果'
                }

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                analysis_data = results.get('results', {})

                # 导出各种分析类型的统计结果
                if 'points' in analysis_data:
                    points_df = analysis_data['points']['statistics']
                    points_df.to_excel(writer, sheet_name='点统计', index=False)

                if 'lines' in analysis_data:
                    lines_df = analysis_data['lines']['statistics']
                    lines_df.to_excel(writer, sheet_name='线统计', index=False)

                if 'polygons' in analysis_data:
                    polygons_df = analysis_data['polygons']['statistics']
                    polygons_df.to_excel(writer, sheet_name='面统计', index=False)

                # 导出汇总信息
                summary_data = []
                for analysis_type, result in analysis_data.items():
                    summary = result.get('summary', {})
                    summary_data.append({
                        '分析类型': analysis_type,
                        '总要素数': result.get(f'total_{analysis_type}', 0),
                        '已分配要素数': result.get(f'assigned_{analysis_type}', 0),
                        '未分配要素数': result.get(f'unassigned_{analysis_type}', 0),
                        '包含要素的面数': summary.get('polygons_with_{analysis_type}', 0),
                        '每个面平均要素数': summary.get(f'avg_{analysis_type}_per_polygon', 0),
                        '每个面最大要素数': summary.get(f'max_{analysis_type}_per_polygon', 0)
                    })

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='汇总', index=False)

            return {
                'success': True,
                'output_path': output_path,
                'exported_sheets': list(analysis_data.keys()) + ['汇总']
            }

        except ImportError:
            return {
                'success': False,
                'error': '需要安装openpyxl库以支持Excel导出: pip install openpyxl'
            }
        except Exception as e:
            self.logger.error(f"导出Excel文件失败: {e}")
            return {
                'success': False,
                'error': f'导出Excel文件失败: {str(e)}'
            }


if __name__ == "__main__":
    # 测试代码
    analyzer = SpatialAnalyzer()

    # 测试面图层加载
    polygon_result = analyzer.load_polygons_layer("test_polygons.shp")
    print(f"面图层加载结果: {polygon_result}")

    # 测试目标图层加载
    target_result = analyzer.load_target_layer("test_targets.shp")
    print(f"目标图层加载结果: {target_result}")

    # 执行空间分析
    if polygon_result['success'] and target_result['success']:
        analysis_result = analyzer.perform_spatial_analysis()
        print(f"空间分析结果: {analysis_result}")

        # 测试导出功能
        if analysis_result['success']:
            shp_export = analyzer.export_results_to_shapefile(analysis_result, "output_results.shp")
            excel_export = analyzer.export_results_to_excel(analysis_result, "output_results.xlsx")
            print(f"SHP导出结果: {shp_export}")
            print(f"Excel导出结果: {excel_export}")

    print("空间分析器测试完成")