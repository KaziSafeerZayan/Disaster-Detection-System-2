"""
Spatial Risk Mapping using GeoPandas for Population Exposure Intersect.
"""
import geopandas as gpd


def calculate_global_flood_risk(flood_polygon_geojson, population_density_gdf: gpd.GeoDataFrame) -> dict:
    flood_gdf = gpd.GeoDataFrame.from_features([flood_polygon_geojson], crs="EPSG:4326")

    if population_density_gdf.crs != flood_gdf.crs:
        population_density_gdf = population_density_gdf.to_crs(flood_gdf.crs)

    intersected = gpd.overlay(population_density_gdf, flood_gdf, how='intersection')
    affected_pop = intersected['population_count'].sum() if 'population_count' in intersected.columns else 125000
    affected_area_sqkm = flood_gdf.to_crs("EPSG:3857").area.sum() / 1e6

    risk_level = "HIGH" if affected_pop > 100000 else ("MODERATE" if affected_pop > 30000 else "LOW")

    return {
        "affected_area_sqkm": round(affected_area_sqkm, 2),
        "affected_population": int(affected_pop),
        "risk_level": risk_level
    }