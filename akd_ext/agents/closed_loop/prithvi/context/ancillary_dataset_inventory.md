# Ancillary Dataset Inventory with API Access Registry
## Combined Companion Document for the Feasibility Mapper and Workflow Spec Builder

This document has two parts:

**Part 1 — Dataset Descriptions** (Section 1–14): What each dataset measures, provider, spatial/temporal resolution, coverage, key variables, and primary access notes. Use this to determine whether a dataset can satisfy a specific data requirement.

**Part 2 — API Access Details** (Section 15 onward): Programmatic access endpoints, STAC collection IDs, Python packages, authentication requirements, and code examples for each dataset. Use this to specify how to fetch the data.

Both parts are organized by the same domain categories and use the same dataset names. To assess a data requirement: (1) find the dataset in Part 1 to confirm it provides what's needed, then (2) find the same dataset in Part 2 to confirm how to access it.

---

# PART 1 — DATASET DESCRIPTIONS

# **Ancillary Dataset Inventory for the Feasibility Mapper**

## **Companion to Stage 2.2 Context Document**

This document catalogs widely used, publicly accessible geospatial datasets that complement Prithvi-EO-2.0 outputs. The Feasibility Mapper should reference this inventory when assessing data requirements for research questions. Datasets are organized by domain. For each dataset: name, provider, spatial/temporal resolution, coverage, key variables, and primary access method(s) are provided.

## **1\. Climate and Weather Reanalysis**

**ERA5 / ERA5-Land** Provider: ECMWF / Copernicus Climate Data Store Resolution: 0.25° (\~31 km) hourly for ERA5; 0.1° (\~9 km) hourly for ERA5-Land Coverage: Global, 1940–present (ERA5); 1950–present (ERA5-Land) Key Variables: 2m temperature, precipitation, wind (u/v), surface pressure, soil temperature (4 layers), soil moisture (4 layers), snow depth, radiation (shortwave/longwave), evaporation, boundary layer height, 100+ atmospheric variables on 37 pressure levels Access: CDS API (`pip install cdsapi`), requires free ECMWF account URL: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels API: https://cds.climate.copernicus.eu/how-to-api Also on: Google Earth Engine (`ECMWF/ERA5_LAND/HOURLY`), Microsoft Planetary Computer

**MERRA-2 (Modern-Era Retrospective Analysis for Research and Applications)** Provider: NASA GMAO / GES DISC Resolution: 0.5° × 0.625° (\~50 km), hourly Coverage: Global, 1980–present Key Variables: Temperature, humidity, wind, precipitation, radiation, aerosols, ozone, soil moisture, surface fluxes, 70+ atmospheric variables on 72 pressure levels Access: NASA GES DISC (HTTPS, OPeNDAP), requires NASA Earthdata login URL: https://disc.gsfc.nasa.gov/datasets?project=MERRA-2 API: OPeNDAP subsetting via GES DISC

**TerraClimate** Provider: University of Idaho / Climatology Lab Resolution: \~4 km (1/24°), monthly Coverage: Global terrestrial, 1958–present Key Variables: Max/min temperature, precipitation, actual/reference evapotranspiration, soil moisture, climate water deficit, PDSI (Palmer Drought Severity Index), runoff, snow water equivalent, vapor pressure deficit, wind speed, solar radiation Access: THREDDS server (NetCDF), Google Earth Engine (`IDAHO_EPSCOR/TERRACLIMATE`), Microsoft Planetary Computer URL: https://www.climatologylab.org/terraclimate.html Note: v1.1 uses ERA5 as parent dataset. Includes future projections at \+2°C and \+4°C.

**gridMET** Provider: University of Idaho / Climatology Lab Resolution: \~4 km (1/24°), daily Coverage: Contiguous US, 1979–present Key Variables: Daily max/min temperature, precipitation, wind speed, humidity, shortwave radiation, reference ET, VPD, fuel moisture (ERC, BI, FM100, FM1000) Access: THREDDS, Google Earth Engine (`IDAHO_EPSCOR/GRIDMET`) URL: https://www.climatologylab.org/gridmet.html Note: Includes fire danger indices (ERC, Burning Index, fuel moisture) — directly relevant for wildfire RQs.

**Daymet** Provider: NASA ORNL DAAC Resolution: 1 km, daily Coverage: North America, 1980–present Key Variables: Daily min/max temperature, precipitation, shortwave radiation, vapor pressure, snow water equivalent, day length Access: NASA Earthdata / ORNL DAAC, AppEEARS, THREDDS URL: https://daymet.ornl.gov/ API: AppEEARS API (https://appeears.earthdatacloud.nasa.gov/api/)

**CHIRPS (Climate Hazards group InfraRed Precipitation with Station data)** Provider: UC Santa Barbara / USGS Resolution: 0.05° (\~5 km), daily and pentad Coverage: 50°S–50°N (quasi-global land), 1981–present Key Variables: Precipitation Access: HTTPS download, Google Earth Engine (`UCSB-CHG/CHIRPS/DAILY`), IRI Data Library URL: https://www.chc.ucsb.edu/data/chirps Note: Widely used for food security and drought monitoring in data-sparse regions (Africa, Asia).

**PRISM (Parameter-elevation Regressions on Independent Slopes Model)** Provider: Oregon State University / PRISM Climate Group Resolution: 800 m (daily), 4 km (monthly/normals) Coverage: Contiguous US, 1895–present (monthly), 1981–present (daily) Key Variables: Precipitation, max/min temperature, mean dew point, VPD Access: PRISM Climate Group bulk download (HTTPS) URL: https://prism.oregonstate.edu/recent/ Download: https://prism.oregonstate.edu/downloads/

**CFSR / CFSv2 (Climate Forecast System Reanalysis)** Provider: NOAA NCEP Resolution: 0.5° (CFSR), 0.2° (CFSv2), 6-hourly Coverage: Global, 1979–2011 (CFSR), 2011–present (CFSv2) Key Variables: Temperature, wind, humidity, precipitation, radiation, soil moisture, pressure — 100+ variables on pressure levels Access: NOMADS (NOAA Operational Model Archive) URL: https://www.ncei.noaa.gov/products/weather-climate-models/climate-forecast-system NOMADS: https://nomads.ncep.noaa.gov/

**GFS (Global Forecast System)** Provider: NOAA NCEP Resolution: 0.25° (\~25 km), 3-hourly forecasts up to 384 hours Coverage: Global, real-time operational Key Variables: Temperature, wind, humidity, precipitation, pressure, cloud cover — forecast fields Access: NOMADS (HTTPS/OPeNDAP) URL: https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast NOMADS: https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/

**GSMaP (Global Satellite Mapping of Precipitation)** Provider: JAXA Resolution: 0.1° (\~10 km), hourly Coverage: Global (60°N–60°S), 2000–present Key Variables: Precipitation rate Access: JAXA G-Portal URL: https://sharaku.eorc.jaxa.jp/GSMaP/ G-Portal: https://gportal.jaxa.jp/gpr/

## **2\. Land Surface Models and Hydrology**

**GLDAS (Global Land Data Assimilation System)** Provider: NASA GSFC / GES DISC Resolution: 0.25° (\~25 km), 3-hourly and monthly Coverage: Global, 1948–present (Noah model) Key Variables: Soil moisture (4 layers), soil temperature, evapotranspiration, surface/subsurface runoff, snow water equivalent, canopy water, sensible/latent heat flux Access: NASA GES DISC (HTTPS, OPeNDAP, Giovanni) URL: https://ldas.gsfc.nasa.gov/gldas API: GES DISC subset service, Giovanni for visualization

**NLDAS-2 / NLDAS-3 (North American Land Data Assimilation System)** Provider: NASA GSFC / GES DISC Resolution: 0.125° (\~12 km) for NLDAS-2; 1 km for NLDAS-3 (in development) Coverage: North America (CONUS \+ parts of Canada/Mexico), 1979–present Key Variables: Forcing (precipitation, temperature, wind, radiation, humidity) \+ Noah model output (soil moisture, ET, runoff, snow, surface energy budget) Access: NASA GES DISC (HTTPS, OPeNDAP, Giovanni) URL: https://ldas.gsfc.nasa.gov/nldas

**FLDAS (Famine Early Warning Systems Network Land Data Assimilation System)** Provider: NASA GSFC / GES DISC Resolution: 0.1° (\~10 km), monthly Coverage: Africa, Central America, Central/South Asia, 1982–present Key Variables: Soil moisture, ET, runoff, surface energy fluxes (from Noah and VIC models) Access: NASA GES DISC URL: https://ldas.gsfc.nasa.gov/fldas Note: Specifically designed for food security monitoring in developing regions.

**GRACE / GRACE-FO (Gravity Recovery and Climate Experiment)** Provider: NASA/DLR / JPL/CSR/GFZ Resolution: \~300 km (mascon solutions can be \~100 km), monthly Coverage: Global, 2002–2017 (GRACE), 2018–present (GRACE-FO) Key Variables: Terrestrial water storage anomaly (total column — includes groundwater, soil moisture, snow, surface water) Access: NASA PO.DAAC, GES DISC, JPL GRACE Tellus URL: https://grace.jpl.nasa.gov/data/get-data/ Note: Essential for groundwater depletion, drought, and large-scale water balance studies.

**GPM IMERG (Integrated Multi-satellitE Retrievals for GPM)** Provider: NASA / GES DISC Resolution: 0.1° (\~10 km), half-hourly Coverage: Global (60°N–60°S for V06; near-global for V07), 1998–present (TRMM era merged) Key Variables: Precipitation rate, precipitation accumulation, quality flags Access: NASA GES DISC (HTTPS, OPeNDAP), Giovanni, Google Earth Engine (`NASA/GPM_L3/IMERG_V07`) URL: https://gpm.nasa.gov/data/imerg Also: GeoTIFF NRT data at https://jsimpsonhttps.pps.eosdis.nasa.gov/imerg/gis/

**SMAP (Soil Moisture Active Passive)** Provider: NASA / NSIDC DAAC Resolution: 9 km (L3/L4), 36 km (L2), daily/3-hourly Coverage: Global, 2015–present Key Variables: Surface soil moisture (top 5 cm), root zone soil moisture (L4), carbon net ecosystem exchange (L4), freeze/thaw state Access: NASA NSIDC DAAC, AppEEARS URL: https://nsidc.org/data/smap Note: L4 products provide root zone soil moisture and carbon flux — valuable for agriculture and ecology RQs.

**OpenET (Open Evapotranspiration)** Provider: OpenET consortium (EWG, NASA, USGS, universities) Resolution: 30 m (Landsat-based), monthly Coverage: Contiguous US, 2016–present Key Variables: Actual ET from 7 models (DisALEXI, eeMETRIC, geeSEBAL, PT-JPL, SIMS, SSEBop) plus ensemble mean Access: OpenET Explorer, API URL: https://openetdata.org/ API: https://openetdata.org/methodologies/api/ Note: Best available high-resolution ET for US.

## **3\. Agriculture and Crop Data**

**USDA NASS Cropland Data Layer (CDL)** Provider: USDA National Agricultural Statistics Service Resolution: 10 m (2024+), 30 m (2008–2023) Coverage: Contiguous US (CONUS), 2008–present (annual) Key Variables: Crop-specific land cover classification (\~130 categories including corn, soy, wheat, cotton, rice, etc.) Access: CropScape web portal, direct GeoTIFF download, Google Earth Engine (`USDA/NASS/CDL`) URL: https://nassgeodata.gmu.edu/CropScape/ Download: https://www.nass.usda.gov/Research\_and\_Science/Cropland/Release/ API: CropScape REST API (https://nassgeodata.gmu.edu/CropScape/devhelp/help.html)

**USDA NASS Quick Stats (County-Level Agricultural Statistics)** Provider: USDA NASS Resolution: County-level tabular data Coverage: US, varies by survey (annual for most crops) Key Variables: Planted/harvested acreage, yield, production, price — by crop, county, and year Access: Quick Stats API, web query tool URL: https://quickstats.nass.usda.gov/ API: https://quickstats.nass.usda.gov/api/

**GFSAD (Global Food Security Analysis-Support Data)** Provider: USGS / NASA Resolution: 30 m (GFSAD30), 1 km (GFSAD1K) Coverage: Global Key Variables: Cropland extent, crop type, irrigated vs rainfed, crop dominance Access: NASA LP DAAC, USGS URL: https://www.usgs.gov/centers/western-geographic-science-center/science/global-food-security-support-analysis-data-30-m Google Earth Engine: `USGS/GFSAD1000_V1`

**GEOGLAM Crop Monitor / Crop Calendars** Provider: GEOGLAM (Group on Earth Observations) Resolution: National/sub-national, monthly Coverage: Global (major producing countries) Key Variables: Crop condition assessments, crop calendars (planting/growing/harvest dates by region) Access: Web interface, PDF reports URL: https://cropmonitor.org/

**FAO GAEZ (Global Agro-Ecological Zones)** Provider: FAO / IIASA Resolution: \~10 km Coverage: Global Key Variables: Crop suitability, potential yield, agro-ecological zones, land utilization types Access: FAO GAEZ Data Portal URL: https://gaez.fao.org/

**ESA WorldCereal** Provider: ESA / VITO Resolution: 10 m Coverage: Global, 2021 Key Variables: Active cropland, crop type (maize, cereals, winter/spring cereals), irrigation status Access: Terrascope, direct download URL: https://esa-worldcereal.org/

**Canada Annual Crop Inventory (ACI)** Provider: Agriculture and Agri-Food Canada Resolution: 30 m, annual Coverage: Canada, 2009–present Key Variables: Crop type classification (\~70 classes) Access: Open Government Canada URL: https://open.canada.ca/data/en/dataset/ba2645d5-4458-414d-b196-6303ac06c1c9

**NAIP (National Agriculture Imagery Program)** Provider: USDA Farm Service Agency Resolution: 60 cm–1 m, RGB \+ NIR Coverage: Contiguous US (2–3 year cycle) Key Variables: High-resolution aerial imagery (4-band) Access: AWS Open Data, Microsoft Planetary Computer URL: https://naip-usdaonline.hub.arcgis.com/ AWS: https://registry.opendata.aws/naip/

## **4\. Vegetation, Land Cover, and Ecology**

**MODIS Vegetation Products** Provider: NASA LP DAAC Resolution: 250 m–1 km, 8-day/16-day/monthly/annual Coverage: Global, 2000–present Key Products:

* MOD13A1/A2 (NDVI/EVI, 500m/1km, 16-day)  
* MOD15A2H (LAI/FPAR, 500m, 8-day)  
* MOD16A2 (ET/PET, 500m, 8-day)  
* MOD17A2H (GPP, 500m, 8-day)  
* MOD17A3HGF (NPP, 500m, annual)  
* MCD12Q1 (Land Cover Type, 500m, annual)  
* MCD64A1 (Burned Area, 500m, monthly) Access: NASA LP DAAC, AppEEARS, Google Earth Engine URL: https://lpdaac.usgs.gov/ API: AppEEARS API (https://appeears.earthdatacloud.nasa.gov/api/)

**VIIRS Vegetation/Fire Products** Provider: NASA LP DAAC / NOAA Resolution: 375 m–1 km Coverage: Global, 2012–present Key Products: VNP13A1 (NDVI/EVI, 500m, 16-day), VNP21A1D (LST, daily), VNP14IMGTDL\_NRT (active fire) Access: NASA LP DAAC, AppEEARS, FIRMS (for fire)

**ESA WorldCover** Provider: ESA Resolution: 10 m Coverage: Global, 2020 and 2021 Key Variables: 11-class land cover map (tree cover, shrubland, grassland, cropland, built-up, water, etc.) Access: Direct download, Google Earth Engine URL: https://esa-worldcover.org/en

**NLCD (National Land Cover Database)** Provider: USGS / MRLC Resolution: 30 m Coverage: CONUS, 2001/2004/2006/2008/2011/2013/2016/2019/2021 Key Variables: Land cover (16 classes), impervious surface, tree canopy cover Access: MRLC viewer, direct download, Google Earth Engine (`USGS/NLCD_RELEASES/2021_REL/NLCD`) URL: https://www.mrlc.gov/

**Global Forest Watch / Hansen Global Forest Change** Provider: University of Maryland / WRI Resolution: 30 m Coverage: Global, 2000–present (annual loss/gain) Key Variables: Tree cover, forest loss year, forest gain Access: Google Earth Engine (`UMD/hansen/global_forest_change_2023_v1_11`), direct download URL: https://www.globalforestwatch.org/

**GEDI (Global Ecosystem Dynamics Investigation)** Provider: NASA / University of Maryland Resolution: 25 m footprint, gridded at 1 km Coverage: 51.6°N–51.6°S, 2019–present Key Products: Canopy top height (L2A), canopy cover profile (L2B), aboveground biomass density (L4A/L4B) Access: NASA LP DAAC, AppEEARS URL: https://gedi.umd.edu/data/download/ LP DAAC: https://lpdaac.usgs.gov/products/gedi02\_av002/ Note: Only spaceborne lidar for wall-to-wall canopy height and biomass globally.

**Dynamic World** Provider: Google / World Resources Institute Resolution: 10 m, near real-time Coverage: Global, 2015–present Key Variables: 9-class land cover with per-pixel probabilities (water, trees, grass, crops, shrub, flooded vegetation, built area, bare ground, snow/ice) Access: Dynamic World app, direct download via GEE export URL: https://dynamicworld.app/ Paper: https://www.nature.com/articles/s41597-022-01307-4

**BESS (Breathing Earth System Simulator)** Provider: Seoul National University Resolution: 5 km, daily Coverage: Global, 2001–present Key Variables: GPP, ET, PAR (direct/diffuse), surface radiation budget Access: Direct download URL: http://environment.snu.ac.kr/bess/

**NOAA CDR NDVI (Climate Data Record)** Provider: NOAA NCEI Resolution: 0.05° (\~5 km), daily Coverage: Global, 1981–present Key Variables: NDVI, surface reflectance — longest continuous NDVI record (40+ years) Access: NOAA NCEI URL: https://www.ncei.noaa.gov/products/climate-data-records/normalized-difference-vegetation-index

**ALOS PALSAR Forest/Non-Forest Map** Provider: JAXA Resolution: 25 m, annual Coverage: Global, 2007–present Key Variables: Forest/non-forest classification, HH/HV SAR backscatter Access: JAXA EORC URL: https://www.eorc.jaxa.jp/ALOS/en/dataset/fnf\_e.htm

**WRI/Google DeepMind Global Drivers of Forest Loss** Provider: WRI / Google DeepMind Resolution: 30 m, annual Coverage: Global, 2001–2024 Key Variables: Driver of tree cover loss (commodity-driven, shifting agriculture, forestry, wildfire, urbanization) Access: Global Forest Watch URL: https://www.globalforestwatch.org/

**USFS TreeMap** Provider: USDA Forest Service Resolution: 30 m Coverage: CONUS, 2016/2020/2022 Key Variables: Aboveground biomass, basal area, canopy cover, tree species, forest type, carbon stocks Access: USFS GTAC URL: https://www.fs.usda.gov/rds/archive/catalog/RDS-2021-0074

## **5\. Topography and Terrain**

**SRTM (Shuttle Radar Topography Mission)** Provider: NASA / USGS Resolution: 30 m (1 arc-second), 90 m (3 arc-second) Coverage: Global (60°N–56°S) Key Variables: Elevation (DEM) Access: NASA LP DAAC, USGS EarthExplorer, AppEEARS, Google Earth Engine (`USGS/SRTMGL1_003`) URL: https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1

**Copernicus DEM (GLO-30)** Provider: ESA / Copernicus Resolution: 30 m Coverage: Global Key Variables: Elevation Access: AWS Open Data, Microsoft Planetary Computer, Copernicus Data Space URL: https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model

**FABDEM (Forest And Buildings removed DEM)** Provider: University of Bristol Resolution: 30 m Coverage: Global Key Variables: Bare-earth elevation (canopy and building artifacts removed from Copernicus DEM) Access: Direct download URL: https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn

**NASADEM** Provider: NASA JPL Resolution: 30 m Coverage: Global (improved reprocessing of SRTM) Key Variables: Elevation — void-filled and artifact-removed Access: NASA LP DAAC, AppEEARS URL: https://lpdaac.usgs.gov/products/nasadem\_hgtv001/

## **6\. Fire, Burn Severity, and Fuel Moisture**

**NASA FIRMS (Fire Information for Resource Management System)** Provider: NASA LANCE Resolution: 375 m (VIIRS), 1 km (MODIS), NRT Coverage: Global, 2000–present (MODIS), 2012–present (VIIRS) Key Variables: Active fire detections (location, brightness temp, FRP, confidence) Access: HTTPS download (SHP/KML/CSV), WMS, email alerts URL: https://firms.modaps.eosdis.nasa.gov/ API: FIRMS API (https://firms.modaps.eosdis.nasa.gov/api/)

**MTBS (Monitoring Trends in Burn Severity)** Provider: USGS / USFS Resolution: 30 m Coverage: US, 1984–present Key Variables: Burn severity (dNBR), fire perimeters, fire occurrence for fires \>1000 acres (West) or \>500 acres (East) Access: Direct download, interactive viewer URL: https://www.mtbs.gov/

**MODIS/VIIRS Burned Area (MCD64A1 / VNP64A1)** Provider: NASA LP DAAC Resolution: 500 m, monthly Coverage: Global, 2000–present Key Variables: Burn date, uncertainty, quality assessment Access: LP DAAC, AppEEARS, Google Earth Engine (`MODIS/061/MCD64A1`)

**LANDFIRE (Landscape Fire and Resource Management Planning Tools)** Provider: USGS / USFS Resolution: 30 m Coverage: US (including Hawaii, Alaska), updated \~every 2 years Key Variables: Fuel models (13 and 40 classes), canopy cover, canopy height, canopy base height, canopy bulk density, existing vegetation type/cover/height, fire regime, disturbance Access: Direct download, LANDFIRE Map Viewer URL: https://landfire.gov/ Note: Critical for wildfire modeling and fuel moisture RQs.

**FireCCI (ESA Climate Change Initiative Fire)** Provider: ESA CCI Resolution: 250 m, monthly Coverage: Global, 2001–2020 Key Variables: Burned area, date of burn, confidence level Access: ESA CCI Open Data Portal URL: https://climate.esa.int/en/projects/fire/

**GRIDMET Drought Indices** Provider: University of Idaho / Climatology Lab Resolution: \~4 km, various temporal Coverage: Contiguous US, 1980–present Key Variables: PDSI, EDDI, SPI, SPEI at multiple time scales, z-index Access: THREDDS URL: https://www.climatologylab.org/gridmet.html

**SPEIbase (Standardised Precipitation-Evapotranspiration Index)** Provider: CSIC (Spanish Research Council) Resolution: 0.5° (\~50 km), monthly Coverage: Global, 1901–present Key Variables: SPEI at 1–48 month time scales Access: SPEIbase website (NetCDF download) URL: https://spei.csic.es/database.html

## **7\. Soil and Geology**

**SoilGrids** Provider: ISRIC – World Soil Information Resolution: 250 m Coverage: Global Key Variables: Soil organic carbon, bulk density, clay/silt/sand content, pH, CEC, nitrogen — at 6 standard depths (0–200 cm) Access: WCS/WMS, direct download, Google Earth Engine URL: https://soilgrids.org/ API: https://rest.isric.org/soilgrids/v2.0/docs

**gSSURGO / STATSGO2 (US Soils)** Provider: USDA NRCS Resolution: Field-level (gSSURGO), \~1 km (STATSGO2) Coverage: US Key Variables: Hundreds of soil properties (texture, drainage class, AWC, organic matter, hydrologic group, erosion factors) Access: NRCS Geospatial Data Gateway, Web Soil Survey URL: https://datagateway.nrcs.usda.gov/ Web Soil Survey: https://websoilsurvey.nrcs.usda.gov/

**OpenLandMap** Provider: OpenGeoHub Resolution: 250 m–1 km Coverage: Global Key Variables: Soil properties, landform, lithology, land cover, vegetation indices Access: Zenodo download, WCS, Google Earth Engine URL: https://openlandmap.org/

**iSDAsoil (Innovative Solutions for Decision Agriculture)** Provider: iSDA / ISRIC Resolution: 30 m Coverage: Africa Key Variables: 20+ soil properties at 0–20 cm and 20–50 cm: pH, organic carbon, nitrogen, texture, bulk density, CEC, extractable nutrients, depth to bedrock Access: iSDA API, direct download URL: https://isda-africa.com/isdasoil API: https://api.isda-africa.com/v1/soilproperty

## **8\. Water Bodies, Flood, and Hydrology Reference**

**JRC Global Surface Water** Provider: EC Joint Research Centre Resolution: 30 m Coverage: Global, 1984–2021 Key Variables: Water occurrence, change, seasonality, recurrence, transitions Access: Direct download, Google Earth Engine (`JRC/GSW1_4/GlobalSurfaceWater`) URL: https://global-surface-water.appspot.com/

**Global Flood Database (GFD)** Provider: Cloud to Street / Columbia University Resolution: 250 m Coverage: Global, 913 flood events (2000–2018) Key Variables: Flood extent, depth estimation, affected population, duration Access: Google Earth Engine (`GLOBAL_FLOOD_DB/MODIS_EVENTS/V1`) URL: https://global-flood-database.cloudtostreet.ai/

**Dartmouth Flood Observatory** Provider: University of Colorado Resolution: Event-based polygons Coverage: Global, 1985–present Key Variables: Flood extent from satellite (MODIS-based), flood magnitude, affected area Access: Web download URL: https://floodobservatory.colorado.edu/

**HydroSHEDS / HydroBASINS** Provider: WWF / McGill University Resolution: 15 arc-second (\~500 m) Coverage: Global Key Variables: Hydrologically conditioned DEM, flow direction, flow accumulation, river network, basin boundaries (levels 1–12) Access: Direct download URL: https://www.hydrosheds.org/

**OPERA DSWx (Dynamic Surface Water Extent)** Provider: NASA JPL / OPERA project Resolution: 30 m (HLS-based), 100 m (Sentinel-1-based) Coverage: Global, 2023–present Key Variables: Surface water classification (not water, open water, partial surface water, snow/ice, cloud) Access: NASA LP DAAC, AppEEARS URL: https://www.jpl.nasa.gov/go/opera LP DAAC: https://lpdaac.usgs.gov/products/dswx\_hlsv001/ Note: Operational NRT surface water. Direct complement to Prithvi flood detection.

**GFPLAIN250m (Global Floodplain Dataset)** Provider: University of Bristol / IAHS Resolution: 250 m Coverage: Global Key Variables: Binary floodplain extent Access: Zenodo download URL: https://zenodo.org/record/6490774

## **9\. Socioeconomic and Population**

**WorldPop** Provider: University of Southampton Resolution: 100 m and 1 km Coverage: Global, 2000–2020 Key Variables: Population count, population density, age/sex structure, urban change Access: Direct download, HTTPS URL: https://www.worldpop.org/

**GPW (Gridded Population of the World)** Provider: CIESIN / Columbia University / NASA SEDAC Resolution: \~1 km (30 arc-second) Coverage: Global, 2000/2005/2010/2015/2020 Key Variables: Population count, population density Access: NASA SEDAC, AppEEARS URL: https://sedac.ciesin.columbia.edu/data/collection/gpw-v4

**GHSL (Global Human Settlement Layer)** Provider: EC Joint Research Centre Resolution: 10 m (built-up), 100 m–1 km (population) Coverage: Global, multi-epoch (1975–2030) Key Variables: Built-up surface, building height, population grid, settlement model (urban/rural classification) Access: Direct download, Google Earth Engine URL: https://ghsl.jrc.ec.europa.eu/

**FEWS NET (Famine Early Warning Systems Network)** Provider: USAID / USGS / NASA Resolution: National/sub-national (admin boundaries) Coverage: Food-insecure regions (Africa, Central America, Central/South Asia, Caribbean) Key Variables: Integrated food security phase (IPC), crop production estimates, market prices, climate hazards assessment Access: FEWS NET Data Center (web download) URL: https://fews.net/data

**VIIRS Nighttime Lights (Black Marble / EOG)** Provider: NASA / NOAA EOG Resolution: 500 m (Black Marble), 750 m (EOG composites) Coverage: Global, 2012–present (VIIRS), 1992–2013 (DMSP-OLS) Key Variables: Nighttime radiance, stray light corrected Access: NASA Black Marble (LP DAAC), NOAA EOG Black Marble URL: https://blackmarble.gsfc.nasa.gov/ EOG URL: https://eogdata.mines.edu/products/vnl/

**LandScan** Provider: Oak Ridge National Laboratory (ORNL) Resolution: \~1 km, annual Coverage: Global, 2000–present Key Variables: Ambient (24-hour average) population count Access: LandScan website (requires registration) URL: https://landscan.ornl.gov/

**Malaria Atlas Project (MAP) Products** Provider: University of Oxford / MAP Resolution: 1–5 km Coverage: Global (focus on endemic regions) Key Products: Gap-filled EVI, gap-filled LST day/night, Tasseled Cap, accessibility to cities/healthcare, friction surfaces, malaria prevalence Access: MAP website URL: https://malariaatlas.org/ Note: Gap-filled MODIS products are cloud-free globally — useful beyond malaria.

## **10\. Disaster and Hazard Reference**

**EM-DAT (International Disaster Database)** Provider: CRED / UCLouvain Resolution: Event-level (country/region), tabular Coverage: Global, 1900–present Key Variables: Disaster type, date, location, deaths, affected population, economic damage Access: Requires registration URL: https://www.emdat.be/

**NASA Landslide Inventory (Global Landslide Catalog)** Provider: NASA GSFC Resolution: Point locations Coverage: Global, 2007–present Key Variables: Landslide location, trigger, size, date, fatalities Access: NASA Open Data Portal URL: https://data.nasa.gov/Earth-Science/Global-Landslide-Catalog/h9d8-neg4

**USGS Earthquake Hazards (ShakeMap, PAGER)** Provider: USGS Resolution: Event-based Coverage: Global Key Variables: Earthquake magnitude, intensity, shaking, population exposure Access: API, GeoJSON feeds URL: https://earthquake.usgs.gov/data/ API: https://earthquake.usgs.gov/fdsnws/event/1/

## **11\. Ocean and Coastal**

**NOAA OISST (Optimum Interpolation Sea Surface Temperature)** Provider: NOAA NCEI Resolution: 0.25° (\~25 km), daily Coverage: Global ocean, 1981–present Key Variables: Sea surface temperature, sea ice concentration Access: NOAA NCEI, THREDDS URL: https://www.ncei.noaa.gov/products/optimum-interpolation-sst

**Copernicus Marine Service (CMEMS)** Provider: Copernicus / Mercator Ocean Resolution: 0.08°–0.25°, daily Coverage: Global ocean Key Products: Ocean physics (SST, salinity, currents, sea level), biogeochemistry (chlorophyll, nutrients, carbon, dissolved oxygen), waves Access: Copernicus Marine Data Store API (`pip install copernicusmarine`) URL: https://data.marine.copernicus.eu/

**MODIS Ocean Color** Provider: NASA Ocean Biology Processing Group Resolution: 4 km, daily/8-day/monthly Coverage: Global ocean, 2002–present Key Variables: Chlorophyll-a, SST, PAR, diffuse attenuation Access: NASA OceanData URL: https://oceandata.sci.gsfc.nasa.gov/

## **12\. Air Quality and Atmospheric Composition**

**Sentinel-5P TROPOMI** Provider: ESA / Copernicus Resolution: 5.5 × 3.5 km Coverage: Global, 2018–present Key Variables: NO₂, SO₂, CO, CH₄, O₃, HCHO, aerosol index Access: Copernicus Data Space, Google Earth Engine (`COPERNICUS/S5P/OFFL/L3_NO2`) URL: https://dataspace.copernicus.eu/

**CAMS Global Reanalysis (EAC4)** Provider: ECMWF / Copernicus Atmosphere Monitoring Service Resolution: \~80 km, 3-hourly Coverage: Global, 2003–present Key Variables: Aerosol optical depth, PM2.5, PM10, ozone, CO, NO₂, SO₂, dust, fire emissions Access: Copernicus ADS (Atmosphere Data Store) URL: https://ads.atmosphere.copernicus.eu/

## **13\. Global Satellite Embeddings**

Pre-computed vector representations of the Earth's surface from foundation models. These embeddings encode spectral, spatial, and temporal information into compact feature vectors, eliminating the need for manual feature engineering. Useful as input features for classification, regression, change detection, and similarity search — especially in data-sparse regions where labeled training samples are scarce.

**Google/DeepMind AlphaEarth Satellite Embeddings** Provider: Google / Google DeepMind Resolution: 10 m per pixel, 64-dimensional embedding vector Coverage: Global terrestrial \+ coastal, annual layers 2017–2025 (rolling) Input Sources: Multi-sensor fusion (Sentinel-1, Sentinel-2, Landsat 8/9, LiDAR, and others) Key Properties: Each pixel encodes the annual temporal trajectory of surface conditions across multiple sensors. Captures spectral, spatial, and temporal context. Overcomes cloud cover, sensor artifacts, and missing data through learned representations. Consistently outperforms both designed featurization (NDVI, composites) and other learned approaches (SatCLIP, Prithvi, Clay) across diverse tasks. Access: Google Earth Engine (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`) URL: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE\_SATELLITE\_EMBEDDING\_V1\_ANNUAL Also on: HuggingFace (`Major-TOM/Core-AlphaEarth-Embeddings`) License: CC-BY 4.0

**Clay Foundation Model Embeddings** Provider: Clay Foundation (Radiant Earth) Resolution: 10 m per pixel, 768-dimensional embedding vector Coverage: Global (1,203 MGRS tiles for v0; expanding) Input Sources: Sentinel-2 (10 bands), Sentinel-1 (2 bands), DEM (1 band), 3 timesteps per location Key Properties: Vision Transformer (ViT) trained via Masked Autoencoder (MAE). Embeddings encode spatial, temporal, and spectral information. Supports similarity search, fine-tuning for classification/regression/generative tasks. Open source model (Apache license) with pip-installable package. Access: Source Cooperative (pre-computed embeddings), HuggingFace (model weights at `made-with-clay/Clay`), generate on-demand via `pip install clay-model` URL: https://clay-foundation.github.io/model/ Embeddings: https://source.coop/clay/clay-model-v0-embeddings License: Apache 2.0 (model), ODC-BY (embeddings)

**Major TOM Global Embeddings** Provider: Community project (Czerkawski et al.) Resolution: 10 m fragments (\~224×224 pixel chips), multiple models Coverage: Global dense coverage (built on Major TOM Core: \>60 TB Copernicus data) Input Sources: Sentinel-2 L1C, Sentinel-2 L2A, Sentinel-1 RTC Key Properties: Standardized embedding format across multiple foundation models. Four embedding datasets released: SSL4EO-S12 (ResNet50), SoftCon, DINOv2, SatMAE. Enables cross-model comparison at global scale. Community-extensible standard. Access: HuggingFace (`Major-TOM/embeddings`) URL: https://huggingface.co/Major-TOM Paper: https://arxiv.org/abs/2412.05600 License: Open (ODC-BY for data, varies by model)

**SatCLIP (Satellite Contrastive Location-Image Pretraining)** Provider: Microsoft Research / TU Munich Resolution: Location-level (lat/lon → embedding), not pixel-level Coverage: Global (trained on globally sampled Sentinel-2) Input Sources: Sentinel-2 multi-spectral imagery Key Properties: Encodes geographic locations (not images) into vector embeddings that capture environmental and socioeconomic characteristics. Input is lat/lon coordinates → output is embedding vector. Useful for tasks that depend on location but not necessarily imagery (temperature prediction, species distribution, population density). Lightweight and fast inference. Access: GitHub, pip install URL: https://github.com/microsoft/satclip Paper: https://arxiv.org/abs/2311.17179 License: MIT

**SatlasPretrain / Satlas Embeddings** Provider: Allen Institute for AI (AI2) Resolution: Sentinel-2 (10 m) and NAIP (1 m) Coverage: Global (Sentinel-2), US (NAIP) Input Sources: Sentinel-2, NAIP, with labels from OpenStreetMap and other sources Key Properties: Pre-trained on 302M image-label pairs spanning 137 categories (land cover, infrastructure, marine, etc.). Swin Transformer backbone. Designed for fine-tuning on downstream tasks with minimal labeled data. Strong baseline for building/road/solar panel detection, land cover, tree cover. Access: HuggingFace (`allenai/satlas-pretrain`), GitHub URL: https://github.com/allenai/satlas License: Apache 2.0

**TESSERA (Temporal Embeddings of Surface Spectra for Earth Representation and Analysis)** Provider: University of Cambridge Resolution: 10 m per pixel, 128-dimensional embedding vector (int8) Coverage: Global terrestrial, annual layers 2017–2024 Input Sources: Sentinel-1 (SAR) \+ Sentinel-2 (optical), multi-temporal time series Key Properties: Pixel-wise foundation model using Barlow Twins self-supervised learning. Preserves phenological signals lost in compositing. Pre-computed global annual maps. Outperforms or matches PRESTO, AlphaEarth, and task-specific models on crop classification, canopy height, and biomass. Only needs a small MLP or RF on top. CC0 license (completely unrestricted). Access: HuggingFace, GeoTessera Python library (`pip install geotessera`) GitHub: https://github.com/ucam-eo/tessera GeoTessera: https://github.com/ucam-eo/geotessera Paper: https://arxiv.org/abs/2506.20380 License: MIT (software), CC0 (embeddings and weights)

**PRESTO (Pretrained Remote Sensing Transformer)** Provider: NASA Harvest / University of Maryland Resolution: Pixel-level (generates on-demand), 128-dimensional embedding Coverage: Global (trained on globally sampled data) Input Sources: Sentinel-1, Sentinel-2, ERA5 climate, Dynamic World land cover, SRTM DEM Key Properties: Lightweight transformer (\~1M parameters vs hundreds of millions for ViT models). Designed for remote sensing timeseries. Robust to missing sensors/timesteps. 1000× fewer parameters than ViT-based models. Used by ESA WorldCereal for operational crop mapping. Excels at cropland mapping and land cover classification. Access: GitHub, pip install, can generate embeddings in GEE GitHub: https://github.com/nasaharvest/presto HuggingFace: https://huggingface.co/nasaharvest/presto Paper: https://arxiv.org/abs/2304.14065 License: MIT **MOSAIKS (Multi-task Observation using Satellite Imagery & Kitchen Sinks)** Provider: UC Berkeley / Columbia / others Resolution: \~1 km (featurized from Planet imagery) Coverage: Global (sampled), US (dense) Input Sources: Planet imagery (3 m RGB) Key Properties: Uses random convolutional features (not a deep learning model) to create compact feature vectors from satellite imagery. Designed for econometric and social science applications. Extremely lightweight — features can be computed without GPUs. Shown to predict forest cover, population density, income, nighttime lights, and other outcomes. Access: Pre-computed features available, code on GitHub URL: http://www.globalpolicy.science/mosaiks Paper: https://www.nature.com/articles/s41467-021-24638-z License: Open

## **14\. Unified Access Portals (Multi-Dataset)**

**NASA AppEEARS** Datasets: MODIS, VIIRS, SMAP, HLS, ECOSTRESS, Daymet, SRTM, GPW, and more Access: GUI \+ REST API URL: https://appeears.earthdatacloud.nasa.gov/ API: https://appeears.earthdatacloud.nasa.gov/api/ Note: Best single tool for combining NASA datasets. Handles spatial/temporal subsetting and format conversion.

**Google Earth Engine** Datasets: 1000+ public datasets including ERA5, MODIS, Landsat, Sentinel, CDL, CHIRPS, GPM, SRTM, WorldPop, and more Access: Python API (`earthengine-api`), JavaScript Code Editor URL: https://earthengine.google.com/ Catalog: https://developers.google.com/earth-engine/datasets/

**Microsoft Planetary Computer** Datasets: Landsat, Sentinel, MODIS, ERA5, TerraClimate, NAIP, Copernicus DEM, and more Access: STAC API, Jupyter Hub URL: https://planetarycomputer.microsoft.com/catalog

**NASA Giovanni** Datasets: 2000+ variables from GES DISC (MERRA-2, GPM, GLDAS, NLDAS, AIRS, OMI, TRMM) Access: Web-based visualization and analysis (no code needed), supports time-series, maps, scatter plots URL: https://giovanni.gsfc.nasa.gov/giovanni/

**NASA Earthdata Search** Datasets: All NASA EOSDIS holdings (\~75+ PB) Access: Web search \+ download, CMR API for programmatic access URL: https://search.earthdata.nasa.gov/ CMR API: https://cmr.earthdata.nasa.gov/search/

**Copernicus Data Space Ecosystem** Datasets: Sentinel-1/2/3/5P, ERA5, Copernicus DEM, land/ocean/atmosphere services Access: Browser, OData API, OpenSearch, S3 buckets URL: https://dataspace.copernicus.eu/


---

# PART 2 — API ACCESS DETAILS

**API Access Registry**

Ancillary Datasets — Programmatic Access Endpoints

For the Feasibility Mapper (Stage 2/5)

This document provides actionable programmatic access details for each dataset. Every entry includes at least one method a developer can use directly in code without manual browser interaction.

# **STAC Catalogs (Unified Access Points)**

These STAC APIs serve as unified gateways to many datasets. Use pystac-client to query all of them.

| STAC Catalog | Endpoint | Auth | Key Collections |
| :---- | :---- | :---- | :---- |
| NASA CMR (LP DAAC) | cmr.earthdata.nasa.gov/stac/LPCLOUD | Earthdata Login | HLS, MODIS, VIIRS, GEDI, OPERA |
| NASA CMR (GES DISC) | cmr.earthdata.nasa.gov/stac/GES\_DISC | Earthdata Login | GPM IMERG, MERRA-2, GLDAS, NLDAS, FLDAS |
| NASA CMR (NSIDC) | cmr.earthdata.nasa.gov/stac/NSIDC\_ECS | Earthdata Login | SMAP, GRACE-FO |
| NASA CMR (PO.DAAC) | cmr.earthdata.nasa.gov/stac/POCLOUD | Earthdata Login | GRACE, sea level, ocean |
| NASA CMR (ORNL) | cmr.earthdata.nasa.gov/stac/ORNL\_CLOUD | Earthdata Login | Daymet, ABoVE |
| Planetary Computer | planetarycomputer.microsoft.com/api/stac/v1 | None (public) | ERA5, TerraClimate, Landsat, Sentinel-2, NAIP, DEM |
| Copernicus Data Space | catalogue.dataspace.copernicus.eu/stac | Copernicus acct | Sentinel-1/2/3/5P, Copernicus DEM |
| OpenLandMap | s3.eu-central-1.wasabisys.com/stac/openlandmap/catalog.json | None (public) | 104 soil/veg/terrain/climate layers |
| MAAP | stac.maap-project.org/ | None (public) | GEDI, biomass, forest datasets |

 

# **Per-Dataset Access Details (Top 35\)**

## **1\. ERA5 / ERA5-Land**

| Method | Endpoint / Detail |
| :---- | :---- |
| CDS API (primary) | pip install cdsapi → cdsapi.Client().retrieve('reanalysis-era5-single-levels', {...}) |
| CDS API URL | https://cds.climate.copernicus.eu/api |
| CDS STAC | https://cds.climate.copernicus.eu/stac-browser/ |
| Planetary Computer STAC | Collection: era5-pds → https://planetarycomputer.microsoft.com/api/stac/v1/collections/era5-pds |
| Planetary Computer Zarr | https://goeseuwest.blob.core.windows.net/era5-pds/ (Azure Blob) |
| Auth | Free ECMWF account \+ personal access token in \~/.cdsapirc |
| Python example | client.retrieve('reanalysis-era5-single-levels', {'variable': '2m\_temperature', 'year': '2023', 'month': '01', 'day': '01', 'time': '12:00', 'format': 'netcdf'}, 'output.nc') |

 

## **2\. TerraClimate**

| Method | Endpoint / Detail |
| :---- | :---- |
| THREDDS/OPeNDAP (primary) | https://thredds.northwestknowledge.net/thredds/dodsC/agg\_terraclimate\_{variable}\_1958\_CurrentYear\_GLOBE.nc |
| Planetary Computer STAC | Collection: terraclimate → https://planetarycomputer.microsoft.com/api/stac/v1/collections/terraclimate |
| Planetary Computer Zarr | Zarr store linked from STAC collection |
| Auth | None (public) |
| Variables in URL | Replace {variable} with: tmax, tmin, ppt, aet, def, pet, soil, srad, swe, vap, vpd, ws, PDSI, q |

 

## **3\. gridMET**

| Method | Endpoint / Detail |
| :---- | :---- |
| THREDDS/OPeNDAP (primary) | https://thredds.northwestknowledge.net/thredds/dodsC/agg\_met\_{variable}\_1979\_CurrentYear\_CONUS.nc |
| Planetary Computer STAC | Collection: gridmet → https://planetarycomputer.microsoft.com/api/stac/v1/collections/gridmet |
| Auth | None (public) |
| Variables in URL | Replace {variable} with: tmmn, tmmx, pr, rmax, rmin, sph, srad, vs, th, pet, erc, bi, fm100, fm1000 |

 

## **4\. GRIDMET Drought Indices**

| Method | Endpoint / Detail |
| :---- | :---- |
| THREDDS/OPeNDAP | https://thredds.northwestknowledge.net/thredds/dodsC/agg\_met\_pdsi\_1980\_CurrentYear\_CONUS.nc |
| Auth | None (public) |
| Variables | PDSI, SPI (various scales), SPEI (various scales), EDDI, z-index |

 

## **5\. Daymet**

| Method | Endpoint / Detail |
| :---- | :---- |
| AppEEARS API (primary) | https://appeears.earthdatacloud.nasa.gov/api/ |
| ORNL DAAC THREDDS | https://thredds.daac.ornl.gov/thredds/catalog/ornldaac/2129/catalog.html |
| Planetary Computer STAC | Collection: daymet-daily-na → https://planetarycomputer.microsoft.com/api/stac/v1/collections/daymet-daily-na |
| Planetary Computer Zarr | Zarr stores available for daily/monthly/annual |
| Auth | Earthdata Login (for AppEEARS/ORNL) |

 

## **6\. CHIRPS**

| Method | Endpoint / Detail |
| :---- | :---- |
| HTTPS download (primary) | https://data.chc.ucsb.edu/products/CHIRPS-2.0/global\_daily/tifs/p05/ |
| IRI Data Library | https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/ |
| Auth | None (public) |
| Format | GeoTIFF (daily), NetCDF |

 

## **7\. GLDAS**

| Method | Endpoint / Detail |
| :---- | :---- |
| GES DISC OPeNDAP (primary) | https://hydro1.gesdisc.eosdis.nasa.gov/dods/GLDAS\_NOAH025\_3H.2.1 |
| GES DISC HTTPS | https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS\_NOAH025\_3H.2.1/ |
| NASA CMR STAC | Provider: GES\_DISC → search for GLDAS\_NOAH025\_3H |
| Giovanni | https://giovanni.gsfc.nasa.gov/giovanni/ (web visualization) |
| Auth | Earthdata Login |

 

## **8\. NLDAS-2**

| Method | Endpoint / Detail |
| :---- | :---- |
| GES DISC OPeNDAP | https://hydro1.gesdisc.eosdis.nasa.gov/dods/NLDAS\_FORA0125\_H.002 (forcing) |
| GES DISC OPeNDAP | https://hydro1.gesdisc.eosdis.nasa.gov/dods/NLDAS\_NOAH0125\_H.002 (Noah output) |
| GES DISC HTTPS | https://hydro1.gesdisc.eosdis.nasa.gov/data/NLDAS/ |
| Auth | Earthdata Login |

 

## **9\. FLDAS**

| Method | Endpoint / Detail |
| :---- | :---- |
| GES DISC OPeNDAP | https://hydro1.gesdisc.eosdis.nasa.gov/dods/FLDAS\_NOAH01\_C\_GL\_M.001 |
| GES DISC HTTPS | https://hydro1.gesdisc.eosdis.nasa.gov/data/FLDAS/ |
| Auth | Earthdata Login |

 

## **10\. GPM IMERG**

| Method | Endpoint / Detail |
| :---- | :---- |
| GES DISC OPeNDAP (primary) | https://gpm1.gesdisc.eosdis.nasa.gov/dods/GPM\_3IMERGHH\_07 (half-hourly) |
| GES DISC HTTPS | https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM\_L3/GPM\_3IMERGDF.07/ (daily) |
| NRT GeoTIFF | https://jsimpsonhttps.pps.eosdis.nasa.gov/imerg/gis/early/ |
| Planetary Computer STAC | Collection: gpm-imerg-hhr → https://planetarycomputer.microsoft.com/api/stac/v1/collections/gpm-imerg-hhr |
| Auth | Earthdata Login |

 

## **11\. SMAP**

| Method | Endpoint / Detail |
| :---- | :---- |
| NSIDC DAAC HTTPS (primary) | https://n5eil01u.ecs.nsidc.org/SMAP/SPL3SMP\_E.006/ (L3 daily 9km) |
| AppEEARS API | https://appeears.earthdatacloud.nasa.gov/api/ → products: SPL3SMP\_E.006, SPL4SMGP.008 |
| NASA CMR STAC | Provider: NSIDC\_ECS → search for SPL3SMP\_E |
| Auth | Earthdata Login |

 

## **12\. GRACE / GRACE-FO**

| Method | Endpoint / Detail |
| :---- | :---- |
| JPL GRACE Tellus (primary) | https://podaac-tools.jpl.nasa.gov/drive/files/allData/tellus/L3/mascon/RL06.3/JPL/v04/CRI/ |
| PO.DAAC HTTPS | https://opendap.earthdata.nasa.gov/collections/C2536962485-PODAAC/ |
| Auth | Earthdata Login |

 

## **13\. MODIS Vegetation Products (NDVI, LAI, GPP, ET, Land Cover)**

| Method | Endpoint / Detail |
| :---- | :---- |
| AppEEARS API (primary) | https://appeears.earthdatacloud.nasa.gov/api/ |
| NASA CMR STAC | Provider: LPCLOUD → collections: MOD13A1.061, MOD15A2H.061, MOD17A2H.061, MOD16A2.061, MCD12Q1.061 |
| LP DAAC HTTPS | https://e4ftl01.cr.usgs.gov/MOLT/ (Terra), https://e4ftl01.cr.usgs.gov/MOLA/ (Aqua) |
| Planetary Computer STAC | Collections: modis-13A1-061 (NDVI), modis-17A2H-061 (GPP), etc. |
| Auth | Earthdata Login |
| Python | appeears package or earthaccess package: pip install earthaccess |

 

## **14\. VIIRS Products**

| Method | Endpoint / Detail |
| :---- | :---- |
| AppEEARS API | Same as MODIS — https://appeears.earthdatacloud.nasa.gov/api/ |
| NASA CMR STAC | Provider: LPCLOUD → collections: VNP13A1.002, VNP21A1D.002 |
| Auth | Earthdata Login |

 

## **15\. USDA NASS CDL**

| Method | Endpoint / Detail |
| :---- | :---- |
| CropScape REST API (primary) | https://nassgeodata.gmu.edu/CropScape/devhelp/help.html |
| Direct GeoTIFF download | https://www.nass.usda.gov/Research\_and\_Science/Cropland/Release/ |
| Example API call | https://nassgeodata.gmu.edu/CropScape/NASS\_CDL\_API.php?year=2023\&fips=17 (Illinois) |
| Auth | None (public) |

 

## **16\. USDA NASS Quick Stats**

| Method | Endpoint / Detail |
| :---- | :---- |
| REST API (primary) | https://quickstats.nass.usda.gov/api/ |
| API key required | Register at https://quickstats.nass.usda.gov/api/ |
| Example | https://quickstats.nass.usda.gov/api/api\_GET/?key=YOUR\_KEY\&commodity\_desc=CORN\&year=2023\&state\_alpha=IL\&format=JSON |

 

## **17\. ESA WorldCover**

| Method | Endpoint / Detail |
| :---- | :---- |
| Planetary Computer STAC (primary) | Collection: esa-worldcover → https://planetarycomputer.microsoft.com/api/stac/v1/collections/esa-worldcover |
| AWS Open Data | s3://esa-worldcover/ |
| Copernicus STAC | https://catalogue.dataspace.copernicus.eu/stac |
| Auth | None (public) |

 

## **18\. NLCD**

| Method | Endpoint / Detail |
| :---- | :---- |
| MRLC direct download (primary) | https://www.mrlc.gov/data |
| AWS S3 | s3://mrlc/ (COG format) |
| Planetary Computer STAC | Collection: nlcd |
| Auth | None (public) |

 

## **19\. Hansen Global Forest Change**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct HTTPS (primary) | https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/ |
| Tile pattern | Hansen\_GFC-2023-v1.11\_{variable}\_{lat}\_{lon}.tif |
| Variables | treecover2000, lossyear, gain, datamask |
| Auth | None (public) |

 

## 

## 

## **20\. GEDI**

| Method | Endpoint / Detail |
| :---- | :---- |
| AppEEARS API (primary) | https://appeears.earthdatacloud.nasa.gov/api/ → products: GEDI02\_A.002, GEDI04\_A.002 |
| NASA CMR STAC | Provider: LPCLOUD → collections: GEDI02\_A.002, GEDI02\_B.002, GEDI04\_A.002 |
| LP DAAC HTTPS | https://e4ftl01.cr.usgs.gov/GEDI/ |
| earthaccess | pip install earthaccess → earthaccess.search\_data(short\_name='GEDI02\_A', version='002') |
| Auth | Earthdata Login |

 

## **21\. SRTM**

| Method | Endpoint / Detail |
| :---- | :---- |
| Planetary Computer STAC (primary) | Collection: nasadem → https://planetarycomputer.microsoft.com/api/stac/v1/collections/nasadem |
| AppEEARS API | Product: SRTMGL1\_NC.003 |
| AWS Open Data | s3://elevation-tiles-prod/ |
| Auth | None (Planetary Computer), Earthdata Login (AppEEARS) |

 

## **22\. Copernicus DEM GLO-30**

| Method | Endpoint / Detail |
| :---- | :---- |
| Planetary Computer STAC (primary) | Collection: cop-dem-glo-30 → https://planetarycomputer.microsoft.com/api/stac/v1/collections/cop-dem-glo-30 |
| AWS Open Data | s3://copernicus-dem-30m/ |
| Copernicus Data Space | https://catalogue.dataspace.copernicus.eu/stac |
| Auth | None (public) |

 

## **23\. NASA FIRMS (Active Fire)**

| Method | Endpoint / Detail |
| :---- | :---- |
| FIRMS REST API (primary) | https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP\_KEY}/VIIRS\_SNPP\_NRT/{bbox}/{days} |
| API key | Register at https://firms.modaps.eosdis.nasa.gov/api/area/ |
| Bulk archive | https://firms.modaps.eosdis.nasa.gov/download/ |
| WMS | https://firms.modaps.eosdis.nasa.gov/wms/ |
| Auth | FIRMS MAP key (free) |

 

## **24\. MTBS (Burn Severity)**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (primary) | https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/MTBS\_Fire/data/composite\_data/burned\_area/ |
| Planetary Computer STAC | Collection: mtbs → https://planetarycomputer.microsoft.com/api/stac/v1/collections/mtbs |
| Auth | None (public) |

 

## **25\. LANDFIRE**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (primary) | https://landfire.gov/getdata.php |
| LANDFIRE Product Service | https://lfps.usgs.gov/arcgis/rest/services/ |
| Auth | None (public) |

 

## **26\. SoilGrids**

| Method | Endpoint / Detail |
| :---- | :---- |
| WCS API (primary) | https://maps.isric.org/mapserv?map=/map/{variable}.map\&SERVICE=WCS\&VERSION=2.0.1\&REQUEST=GetCoverage |
| REST API | https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}\&lat={lat}\&property={prop}\&depth={depth} |
| API docs | https://rest.isric.org/soilgrids/v2.0/docs |
| Auth | None (public) |
| Properties | bdod, cec, cfvo, clay, nitrogen, ocd, ocs, phh2o, sand, silt, soc |

 

## **27\. OpenLandMap (104 layers)**

| Method | Endpoint / Detail |
| :---- | :---- |
| STAC Catalog (primary) | https://s3.eu-central-1.wasabisys.com/stac/openlandmap/catalog.json |
| STAC Browser | https://stac.openlandmap.org/ |
| WCS | https://geoserver.opengeohub.org/landgisgeoserver/ows?service=WCS |
| S3 direct (COG) | Follow href in STAC items for direct COG access |
| Auth | None (public) |

 

## **28\. JRC Global Surface Water**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (primary) | https://global-surface-water.appspot.com/download |
| Tile pattern | https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/occurrence\_{lon}\_{lat}.tif |
| Auth | None (public) |

 

## **29\. OPERA DSWx**

| Method | Endpoint / Detail |
| :---- | :---- |
| NASA CMR STAC (primary) | Provider: LPCLOUD → collection: OPERA\_L3\_DSWX-HLS\_V1 |
| LP DAAC HTTPS | https://e4ftl01.cr.usgs.gov/OPS/OPERA\_L3\_DSWx-HLS\_V1/ |
| earthaccess | earthaccess.search\_data(short\_name='OPERA\_L3\_DSWX-HLS', version='1') |
| Auth | Earthdata Login |

 

## **30\. Sentinel-5P TROPOMI**

| Method | Endpoint / Detail |
| :---- | :---- |
| Copernicus STAC (primary) | https://catalogue.dataspace.copernicus.eu/stac → collection: SENTINEL-5P |
| Copernicus OData API | https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-5P' |
| S5P-PAL | http://www.tropomi.eu/data-products/ (processed products) |
| Auth | Copernicus account |

 

## **31\. WorldPop**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct HTTPS (primary) | https://data.worldpop.org/GIS/Population/Global\_2000\_2020/ |
| API | https://hub.worldpop.org/rest/data/pop/ |
| Auth | None (public) |

 

## **32\. GHSL**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (primary) | https://ghsl.jrc.ec.europa.eu/download.php |
| Tile download | Select product → resolution → epoch → download tiles |
| Auth | None (public) |

 

## **33\. NOAA OISST**

| Method | Endpoint / Detail |
| :---- | :---- |
| THREDDS/OPeNDAP (primary) | https://www.ncei.noaa.gov/thredds/dodsC/OisstBase/NetCDF/V2.1/AVHRR/ |
| HTTPS | https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/ |
| Auth | None (public) |

 

## **34\. Copernicus Marine Service (CMEMS)**

| Method | Endpoint / Detail |
| :---- | :---- |
| Python package (primary) | pip install copernicusmarine → copernicusmarine.subset(dataset\_id='...', variables=\['...'\]) |
| Marine Data Store | https://data.marine.copernicus.eu/ |
| Auth | Copernicus Marine account |

 

## **35\. Satellite Embeddings**

**Google AlphaEarth**

**Clay**

**TESSERA**

**PRESTO**

**SatCLIP**

**MOSAIKS**

| Method | Endpoint / Detail |
| :---- | :---- |
| HuggingFace (primary) | https://huggingface.co/datasets/Major-TOM/Core-AlphaEarth-Embeddings |
| Note | Also available in Google Earth Engine (GOOGLE/SATELLITE\_EMBEDDING/V1/ANNUAL) but not downloadable via API |
| Method | Endpoint / Detail |
| Source Cooperative (embeddings) | https://source.coop/clay/clay-model-v0-embeddings |
| HuggingFace (model) | https://huggingface.co/made-with-clay/Clay |
| Python package | pip install clay-model → generate on-demand |
| Method | Endpoint / Detail |
| GeoTessera Python (primary) | pip install geotessera → geoai.tessera\_download(bbox=(...), year=2024) |
| HuggingFace | https://huggingface.co/ucam-eo/tessera (model weights) |
| GitHub | https://github.com/ucam-eo/tessera |
| Method | Endpoint / Detail |
| GitHub (primary) | https://github.com/nasaharvest/presto |
| HuggingFace | https://huggingface.co/nasaharvest/presto |
| Python | pip install presto-light → generate embeddings on-demand |
| Method | Endpoint / Detail |
| GitHub (primary) | https://github.com/microsoft/satclip |
| Python | pip installable, generates location embeddings from lat/lon |
| Method | Endpoint / Detail |
| Pre-computed features | http://www.globalpolicy.science/mosaiks |
| GitHub | Code for generating features from imagery |

 

# **Remaining Datasets (36–87)**

## **36\. MERRA-2**

| Method | Endpoint / Detail |
| :---- | :---- |
| GES DISC HTTPS (primary) | https://data.gesdisc.earthdata.nasa.gov/data/MERRA2/M2T1NXSLV.5.12.4/{year}/{month}/ |
| OPeNDAP (cloud) | https://opendap.earthdata.nasa.gov/collections/C1276812863-GES\_DISC/granules/ |
| OPeNDAP (legacy) | https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/ |
| earthaccess | earthaccess.search\_data(short\_name='M2T1NXSLV', version='5.12.4') |
| NASA CMR STAC | Provider: GES\_DISC |
| Auth | Earthdata Login |
| Key collections | M2T1NXSLV (surface), M2T1NXRAD (radiation), M2T1NXAER (aerosol), M2T3NVASM (3D atmosphere) |

 

## 

## **37\. PRISM**

| Method | Endpoint / Detail |
| :---- | :---- |
| Bulk HTTPS download (primary) | https://prism.oregonstate.edu/fetchData.php?type=bil\&kind=recent\&elem={var}\&temporal=daily\&year={YYYY}\&mon={MM}\&day={DD} |
| AppEEARS | Product available in AppEEARS |
| Auth | None (public download, but uses session-based download links) |
| Note | No REST/STAC API. Download is via HTTP form-based file access. Programmatic download requires scripting the file URL pattern. |

 

## **38\. CFSR / CFSv2**

| Method | Endpoint / Detail |
| :---- | :---- |
| NOMADS OPeNDAP (primary) | https://nomads.ncep.noaa.gov/dods/ |
| CFSR OPeNDAP | https://nomads.ncep.noaa.gov/dods/cfsr |
| CFSv2 OPeNDAP | https://nomads.ncep.noaa.gov/dods/cfs\_v2\_anl\_6h\_flxf |
| HTTPS bulk | https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/ |
| Auth | None (public) |

 

## **39\. GFS**

| Method | Endpoint / Detail |
| :---- | :---- |
| NOMADS OPeNDAP (primary) | https://nomads.ncep.noaa.gov/dods/gfs\_0p25/ |
| HTTPS bulk | https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/ |
| Auth | None (public) |

 

## **40\. GSMaP**

| Method | Endpoint / Detail |
| :---- | :---- |
| JAXA G-Portal (primary) | https://gportal.jaxa.jp/gpr/ |
| Auth | JAXA G-Portal account (free) |
| Note | No public OPeNDAP or STAC endpoint. Download via G-Portal web interface or FTP after registration. |

 

## 

## **41\. OpenET**

| Method | Endpoint / Detail |
| :---- | :---- |
| OpenET API (primary) | https://openet-api.org/ |
| API docs | https://open-et.github.io/docs/ |
| Auth | API key (free registration at openetdata.org) |
| Note | Need to verify current API base URL — was previously https://openet-api.org/raster/timeseries/. Check https://openetdata.org/methodologies/api/ for latest docs. |

 

## **42\. GFSAD**

| Method | Endpoint / Detail |
| :---- | :---- |
| LP DAAC HTTPS (primary) | https://e4ftl01.cr.usgs.gov/MEASURES/GFSAD30NACE.001/ |
| AppEEARS | Product: GFSAD30NACE.001 |
| NASA CMR STAC | Provider: LPCLOUD |
| Auth | Earthdata Login |

 

## **43\. GEOGLAM Crop Monitor**

| Method | Endpoint / Detail |
| :---- | :---- |
| Web reports only | https://cropmonitor.org/index.php/cmreports/reports-archive/ |
| Auth | None |
| Note | No programmatic API. Data is distributed as PDF reports and web maps. Not machine-readable. |

 

## **44\. FAO GAEZ**

| Method | Endpoint / Detail |
| :---- | :---- |
| GAEZ Data Portal | https://gaez.fao.org/api/ |
| Auth | Free FAO account |
| Note | Need to verify if REST API is publicly documented. Data portal has a download interface at https://gaez.fao.org/pages/data-viewer. |

 

## 

## 

## **45\. ESA WorldCereal**

| Method | Endpoint / Detail |
| :---- | :---- |
| Terrascope download (primary) | https://viewer.esa-worldcereal.org/ |
| VITO Terrascope | https://services.terrascope.be/catalogue/ |
| Auth | Terrascope account |
| Note | Direct STAC/API access needs verification. Primary access through Terrascope portal or GEE. |

 

## **46\. Canada ACI**

| Method | Endpoint / Detail |
| :---- | :---- |
| Open Government Canada (primary) | https://open.canada.ca/data/en/dataset/ba2645d5-4458-414d-b196-6303ac06c1c9 |
| WCS/WMS | https://www.agr.gc.ca/atlas/rest/services/mapservices/aci\_crop\_type\_class\_{year}/MapServer |
| Auth | None (public) |

 

## **47\. NAIP**

| Method | Endpoint / Detail |
| :---- | :---- |
| Planetary Computer STAC (primary) | Collection: naip → https://planetarycomputer.microsoft.com/api/stac/v1/collections/naip |
| AWS Open Data | s3://naip-visualization/ and s3://naip-analytic/ |
| Auth | None (public) |

 

## **48\. Dynamic World**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (COG tiles) | Available via GEE export only |
| Auth | Google account (for GEE) |
| Note | No public STAC or download API outside GEE. Data is produced in GEE and must be exported. Source code and methodology at https://github.com/google/dynamicworld. |

 

## 

## 

## **49\. BESS**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (primary) | http://environment.snu.ac.kr/bess/ |
| Auth | None |
| Note | No API. Data available as direct file download from university server. Need to verify current download links are active. |

 

## **50\. NOAA CDR NDVI**

| Method | Endpoint / Detail |
| :---- | :---- |
| NCEI THREDDS/OPeNDAP (primary) | https://www.ncei.noaa.gov/thredds/catalog/cdr/ndvi/catalog.html |
| HTTPS | https://www.ncei.noaa.gov/data/avhrr-land-normalized-difference-vegetation-index/access/ |
| Auth | None (public) |

 

## **51\. ALOS PALSAR Forest/Non-Forest**

| Method | Endpoint / Detail |
| :---- | :---- |
| Planetary Computer STAC (primary) | Collection: alos-fnf-mosaic → https://planetarycomputer.microsoft.com/api/stac/v1/collections/alos-fnf-mosaic |
| JAXA EORC | https://www.eorc.jaxa.jp/ALOS/en/dataset/fnf\_e.htm |
| Auth | None (Planetary Computer), JAXA account for EORC |

 

## **52\. WRI Drivers of Forest Loss**

| Method | Endpoint / Detail |
| :---- | :---- |
| GFW Data API | https://data-api.globalforestwatch.org/ |
| Direct tiles | Available via GFW tile server |
| Auth | None (public) |
| Note | GFW Data API documentation at https://www.globalforestwatch.org/help/developers/. Need to verify current endpoints for driver-of-loss data specifically. |

 

## 

## 

## **53\. USFS TreeMap**

| Method | Endpoint / Detail |
| :---- | :---- |
| USFS Research Data Archive (primary) | https://www.fs.usda.gov/rds/archive/catalog/RDS-2021-0074 |
| Direct download | GeoTIFF files from RDS archive |
| Auth | None (public) |

 

## **54\. FABDEM**

| Method | Endpoint / Detail |
| :---- | :---- |
| University of Bristol (primary) | https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn |
| Auth | None (public) |
| Note | Direct file download only, no API. Large dataset (\~1 TB). |

 

## **55\. NASADEM**

| Method | Endpoint / Detail |
| :---- | :---- |
| Planetary Computer STAC (primary) | Collection: nasadem → https://planetarycomputer.microsoft.com/api/stac/v1/collections/nasadem |
| LP DAAC HTTPS | https://e4ftl01.cr.usgs.gov/MEASURES/NASADEM\_HGT.001/ |
| AppEEARS | Product: NASADEM\_HGT.001 |
| Auth | None (Planetary Computer), Earthdata Login (LP DAAC) |

 

## **56\. FireCCI**

| Method | Endpoint / Detail |
| :---- | :---- |
| CEDA Archive (primary) | https://data.ceda.ac.uk/neodc/esacci/fire/data/burned\_area/MODIS/pixel/v5.1/ |
| CEDA catalog | https://catalogue.ceda.ac.uk/uuid/58f00d8814064b79a0c49662ad3af537/ |
| CDS (cdsapi) | Available via Copernicus Climate Data Store as satellite-fire-burned-area |
| University of Alcala | https://geogra.uah.es/fire\_cci/firecci51.php (download page with continental tiles) |
| Auth | CEDA account (free UK academic) or CDS account (free, global) |
| Coverage | FireCCI51: MODIS 250m, 2001–2022. FireCCIS311 (Sentinel-3 SYN): 300m, 2019–2024 |
| Note | Extended to 2022 as of Feb 2025\. New Sentinel-3 product (v1.1) extends to 2024\. Best accessed via CDS API for programmatic use. |

 

## **57\. SPEIbase**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct NetCDF download (primary) | https://digital.csic.es/handle/10261/288226 |
| Legacy URL | https://spei.csic.es/database.html |
| Auth | None (public) |
| Note | Download is via Zenodo/CSIC digital repository. Single NetCDF file per time scale. |

 

## **58\. gSSURGO / STATSGO2**

| Method | Endpoint / Detail |
| :---- | :---- |
| Soil Data Access REST API (primary) | https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest (POST, JSON) |
| Web Soil Survey | https://websoilsurvey.nrcs.usda.gov/app/ |
| Geospatial Data Gateway | https://datagateway.nrcs.usda.gov/ |
| Auth | None (public) |
| Example | POST to https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest with {"query": "SELECT ... FROM ..."} |

 

## **59\. iSDAsoil**

| Method | Endpoint / Detail |
| :---- | :---- |
| REST API (primary) | https://api.isda-africa.com/isdasoil/v2/soilproperty?lat={lat}\&lon={lon}\&property={prop}\&depth={depth} |
| Layers metadata | https://api.isda-africa.com/isdasoil/v2/layers |
| AWS S3 (bulk) | https://isdasoil.s3.amazonaws.com/soil\_data/{property}/{property}.tif |
| API docs | https://www.isda-africa.com/isdasoil/developer/ |
| Auth | iSDA account (free, token-based) for API; None for S3 |
| Properties | ph, carbon\_organic, nitrogen\_total, clay, sand, silt, bulk\_density, cec, iron\_extractable, potassium\_extractable, calcium\_extractable, magnesium\_extractable, phosphorus\_extractable, sulphur\_extractable, zinc\_extractable, aluminium\_extractable, depth\_to\_bedrock, stone\_content, fcc |

 

## 

## 

## **60\. Global Flood Database**

| Method | Endpoint / Detail |
| :---- | :---- |
| Cloud to Street website | https://global-flood-database.cloudtostreet.ai/ |
| Auth | None |
| Note | Primarily accessed via GEE (GLOBAL\_FLOOD\_DB/MODIS\_EVENTS/V1). No public STAC/API for direct download confirmed. Contact Cloud to Street for bulk access. |

 

## **61\. Dartmouth Flood Observatory**

| Method | Endpoint / Detail |
| :---- | :---- |
| HTTPS download (primary) | https://floodobservatory.colorado.edu/Archives/ |
| Auth | None (public) |
| Note | Shapefiles and KML files organized by year. No API — direct file browsing. |

 

## **62\. HydroSHEDS / HydroBASINS**

| Method | Endpoint / Detail |
| :---- | :---- |
| Direct download (primary) | https://www.hydrosheds.org/products |
| AWS Open Data | s3://hydrosheds/ (some products) |
| Auth | None (public, requires license agreement on website) |

 

## **63\. GFPLAIN250m**

| Method | Endpoint / Detail |
| :---- | :---- |
| Zenodo (primary) | https://zenodo.org/record/6490774 |
| Auth | None (public) |
| Note | Single global raster file, \~250 MB. Direct download from Zenodo. |

 

## **64\. FEWS NET**

| Method | Endpoint / Detail |
| :---- | :---- |
| FEWS NET Data Portal (primary) | https://fews.net/data |
| FDW API | https://fdw.fews.net/api/ |
| Auth | None (public) |
| Note | https://fdw.fews.net/api/ provides REST endpoints for food security data, market prices, crop conditions. |

 

## **65\. VIIRS Nighttime Lights (Black Marble / EOG)**

| Method | Endpoint / Detail |
| :---- | :---- |
| NOAA EOG HTTPS (primary) | https://eogdata.mines.edu/nighttime\_light/annual/v22/ (annual composites) |
| NOAA EOG monthly | https://eogdata.mines.edu/nighttime\_light/monthly\_notile/v10/ |
| NASA Black Marble | LP DAAC: https://e4ftl01.cr.usgs.gov/VIIRS/VNP46A2.002/ |
| AppEEARS | Product: VNP46A2.002 (Black Marble) |
| Auth | Earthdata Login (Black Marble), EOG account (EOG composites) |

 

## **66\. LandScan**

| Method | Endpoint / Detail |
| :---- | :---- |
| ORNL Portal (primary) | https://landscan.ornl.gov/ — free, open access since 2022 (CC BY 4.0) |
| Direct download | GeoTIFF files, no API — download via portal after free account creation |
| GEE Community Catalog | projects/sat-io/open-datasets/ORNL/LANDSCAN\_GLOBAL |
| Auth | Free ORNL account (no restrictions) |
| Note | Was previously restricted; now fully open. Covers 2000–2024. \~1 km global ambient population. |

 

## **67\. Malaria Atlas Project (MAP) Products**

| Method | Endpoint / Detail |
| :---- | :---- |
| MAP website (primary) | https://malariaatlas.org/ |
| R package | install.packages("malariaAtlas") → malariaAtlas::getRaster(surface \= "...", year \= 2020\) |
| Auth | None (R package handles access) |
| Note | Best programmatic access is via the malariaAtlas R package. Python users need to download manually from the website. |

 

## **68\. EM-DAT**

| Method | Endpoint / Detail |
| :---- | :---- |
| EM-DAT website (primary) | https://www.emdat.be/ |
| Auth | Academic registration required |
| Note | No public API. Data export via web query after login. Tabular CSV output. |

 

## **69\. NASA Landslide Catalog**

| Method | Endpoint / Detail |
| :---- | :---- |
| NASA Open Data API (primary) | https://data.nasa.gov/resource/h9d8-neg4.json (Socrata API) |
| Example query | https://data.nasa.gov/resource/h9d8-neg4.json?$where=event\_date \> '2020-01-01'&$limit=1000 |
| Auth | None (public Socrata endpoint) |

 

## **70\. USGS Earthquake Hazards**

| Method | Endpoint / Detail |
| :---- | :---- |
| FDSN Event API (primary) | https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson\&starttime={start}\&endtime={end}\&minmagnitude={mag} |
| Real-time GeoJSON feeds | https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all\_day.geojson (past day) |
| Other feeds | all\_hour.geojson, all\_week.geojson, all\_month.geojson, significant\_month.geojson |
| Auth | None (public) |

 

## **71\. MODIS Ocean Color**

| Method | Endpoint / Detail |
| :---- | :---- |
| NASA OceanData HTTPS (primary) | https://oceandata.sci.gsfc.nasa.gov/ob/getfile/{filename} |
| OPeNDAP | https://oceandata.sci.gsfc.nasa.gov/opendap/ |
| CMR search | earthaccess.search\_data(short\_name='MODISA\_L3m\_OC') |
| Auth | Earthdata Login |

 

## **72\. CAMS Reanalysis (EAC4)**

| Method | Endpoint / Detail |
| :---- | :---- |
| Copernicus ADS API (primary) | pip install cdsapi → retrieve from Atmosphere Data Store |
| ADS URL | https://ads.atmosphere.copernicus.eu/ |
| Auth | Copernicus ADS account |
| Example | client.retrieve('cams-global-reanalysis-eac4', {'variable': 'particulate\_matter\_2.5um', ...}, 'output.nc') |

 

## **73\. SatlasPretrain / Major TOM**

| Method | Endpoint / Detail |
| :---- | :---- |
| SatlasPretrain HuggingFace | https://huggingface.co/allenai/satlas-pretrain |
| SatlasPretrain GitHub | https://github.com/allenai/satlas |
| Major TOM HuggingFace | https://huggingface.co/Major-TOM |
| Auth | None (public) |

 

# **Python Packages for Multi-Dataset Access**

| Package | Install | What It Does |
| :---- | :---- | :---- |
| earthaccess | pip install earthaccess | Unified search/download for all NASA Earthdata (CMR) — HLS, MODIS, VIIRS, GEDI, SMAP, GPM, OPERA |
| pystac-client | pip install pystac-client | Query any STAC API (Planetary Computer, NASA CMR, OpenLandMap, MAAP, Copernicus) |
| cdsapi | pip install cdsapi | ERA5, ERA5-Land from Copernicus CDS |
| copernicusmarine | pip install copernicusmarine | All Copernicus Marine (CMEMS) ocean products |
| planetary-computer | pip install planetary-computer | Sign items from Planetary Computer STAC for download |
| xarray \+ zarr | pip install xarray zarr | Open Zarr stores (ERA5 on Planetary Computer, TerraClimate) directly in memory |
| appeears | Via AppEEARS REST API | Subset MODIS, VIIRS, SMAP, GEDI, Daymet, HLS spatially/temporally |
| geotessera | pip install geotessera | Download/generate TESSERA embeddings |
| odc-stac | pip install odc-stac | Load STAC items as xarray datasets |

# **Authentication Summary**

| Auth System | Datasets Covered | Registration URL |
| :---- | :---- | :---- |
| NASA Earthdata Login | All NASA datasets (MODIS, VIIRS, SMAP, GEDI, GPM, GLDAS, NLDAS, FLDAS, HLS, OPERA, Daymet, GRACE) | https://urs.earthdata.nasa.gov/users/new |
| ECMWF/CDS Account | ERA5, ERA5-Land | https://cds.climate.copernicus.eu/user/register |
| Copernicus Account | Sentinel-1/2/3/5P, Copernicus DEM | https://dataspace.copernicus.eu/ |
| Copernicus Marine | CMEMS ocean products | https://data.marine.copernicus.eu/register |
| FIRMS MAP Key | Active fire data | https://firms.modaps.eosdis.nasa.gov/api/area/ |
| USDA NASS API Key | Quick Stats county-level ag data | https://quickstats.nass.usda.gov/api/ |
| None required | TerraClimate, gridMET, CHIRPS, SoilGrids, OpenLandMap, Hansen GFC, WorldPop, GHSL, JRC Surface Water, SRTM, Copernicus DEM (via PC), ESA WorldCover, NOAA OISST, MTBS, LANDFIRE, all embeddings |   |

   
