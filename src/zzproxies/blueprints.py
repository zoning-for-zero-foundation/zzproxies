# src/zzproxies/blueprints.py

"""
Class functions to generate UPD blueprints from public data sources for defined zzproxies.
Each blueprint class should have:
- __init__(self, bbox, country_code): to set up the bounding box and country code
- run(self): to execute the data fetching and processing, returning UPD-formatted data
- naming convention: Name of Blueprint indicating source
  (e.g., OverturemapBuildingsWithPlaces)
- Class-related special library imports should be included within the particular function in the class
  (to be imported only when the function is called) but generally avoid this.
"""

#general imports for blueprints to share
try:
    import duckdb #we encourage duckdb for in-memory spatial queries
except ModuleNotFoundError:
    duckdb = None
from typing import List, Dict, Any, Optional
import requests


# ----- Blueprint using OvertureMap Foundation (OMF) buildings and places -----
class OvertureMapBuildingsWithPlaces:
    """
    Research Design: Building level UPD derived from OvertureMap Foundation: https://docs.overturemaps.org
    Self-contained helpers for OvertureMap Foundation URL-sources and spatial joins.
    """

    def __init__(self, bbox, country_code):
        if duckdb is None:
            raise ModuleNotFoundError(
                "duckdb is required for OvertureMapBuildingsWithPlaces. Install zzproxies[data]."
            )
        self.bbox = bbox
        self.country_code = country_code
        self.release = self._get_latest_release()  # https://docs.overturemaps.org/release-calendar/
        self.con = duckdb.connect(':memory:')
        self.con.execute("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs;")

        # --- INDUSTRY WEIGHTS & MAPPING for OMF building classification ---
        self.INDUSTRY_MAP = {
                "Retail & Food": ["mall", "shop", "store", "boutique", "kiosk", "grocery", "supermarket", "restaurant", "cafe", "bar", "bakery", "food"],
                "Accommodation": ["hotel", "hostel", "motel", "guest_house", "bed_and_breakfast", "resort", "inn"],
                "Health & Education": ["hospital", "clinic", "pharmacy", "school", "university", "college", "preschool"],
                "Leisure & Culture": ["museum", "gallery", "theatre", "cinema", "stadium", "park", "zoo", "aquarium", "amusement"],
                "Industry & Services": ["warehouse", "factory", "industrial", "logistics", "garage", "bank", "post_office"],
                "Transport": ["stop", "station", "rail", "tram", "bus", "metro", "subway", "ferry", "coach", "terminal", "port", "airport", "transit", "ev_charging"],
                "Other": []
            }

        # Average area-intensity weights for GFA_by_amenity distribution (higher = typically occupies more floor area)
        self.WEIGHT_MAP = {
                "Retail & Food": 1.4,
                "Accommodation": 2.5,
                "Health & Education": 1.2,
                "Leisure & Culture": 1.4,
                "Industry & Services": 2.2,
                "Transport": 0.4,
                "Other": 1.0
            }

    def _get_latest_release(self):
        url = "https://stac.overturemaps.org/catalog.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        latest = data.get("latest")
        if not latest:
            raise RuntimeError("Could not resolve latest Overture release")
        return latest

    def _fetch_from_OMF(self, bbox: List[float]):
        xmin, ymin, xmax, ymax = bbox

        geom_expr = """
            CASE
                WHEN regexp_matches(geometry::TEXT, '^(POLYGON|MULTIPOLYGON|POINT|LINESTRING).*')
                    THEN ST_GeomFromText(geometry::TEXT)
                WHEN geometry::TEXT LIKE '{%"coordinates"%}'
                    THEN ST_GeomFromGeoJSON(geometry::TEXT)
                ELSE ST_GeomFromText('GEOMETRYCOLLECTION EMPTY')
            END
        """

        query = f"""
            WITH bld_base AS (
                SELECT
                    id, subtype, class, num_floors, {geom_expr} as geom,
                    ST_Area_Spheroid({geom_expr}) as area
                FROM read_parquet('s3://overturemaps-us-west-2/release/{self.release}/theme=buildings/type=building/*')
                WHERE bbox.xmin > {xmin} AND bbox.xmax < {xmax}
                AND bbox.ymin > {ymin} AND bbox.ymax < {ymax}
            ),
            -- Calculate modes separately because DuckDB doesn't support mode() OVER()
            subtype_modes AS (
                SELECT num_floors, mode(subtype) as mode_s FROM bld_base GROUP BY num_floors
            ),
            global_subtype_mode AS (
                SELECT mode(subtype) as g_mode_s FROM bld_base
            ),
            floor_modes AS (
                SELECT subtype, class, mode(num_floors) as mode_f FROM bld_base GROUP BY subtype, class
            ),
            global_floor_mode AS (
                SELECT mode(num_floors) as g_mode_f FROM bld_base
            ),
            bld_imputed AS (
                SELECT
                    b.id, b.class, b.geom,
                    b.subtype as original_subtype,
                    b.num_floors as original_floors,
                    COALESCE(b.subtype, sm.mode_s, gsm.g_mode_s) as subtype,
                    COALESCE(b.num_floors, fm.mode_f, gfm.g_mode_f) as num_floors,
                    (b.subtype IS NULL) as is_imputed_subtype,
                    (b.num_floors IS NULL) as is_imputed_floors
                FROM bld_base b
                LEFT JOIN subtype_modes sm ON b.num_floors = sm.num_floors
                CROSS JOIN global_subtype_mode gsm
                LEFT JOIN floor_modes fm ON b.subtype = fm.subtype AND b.class = fm.class
                CROSS JOIN global_floor_mode gfm
            ),
            pts_raw AS (
                SELECT
                    COALESCE(basic_category, 'other') as category,
                    {geom_expr} AS geom,
                    -- We get the building ID that has the LARGEST area for this point
                    -- This prevents double-counting amenities across overlapping polygons
                    b.id as bld_id
                FROM read_parquet('s3://overturemaps-us-west-2/release/{self.release}/theme=places/type=place/*') p
                JOIN bld_base b ON ST_Intersects({geom_expr.replace('geometry', 'p.geometry')}, b.geom)
                WHERE p.bbox.xmin > {xmin} AND p.bbox.xmax < {xmax}
                AND p.bbox.ymin > {ymin} AND p.bbox.ymax < {ymax}
                QUALIFY ROW_NUMBER() OVER(PARTITION BY p.geometry ORDER BY b.area DESC) = 1
            )
            SELECT
                bi.id, bi.subtype, bi.class, bi.num_floors,
                ST_Area_Spheroid(bi.geom) as footprint_area_sqm,
                (ST_Area_Spheroid(bi.geom) * COALESCE(bi.num_floors, 1)) as GFA,
                -- Collect only categories
                list(pts.category) as places,
                ST_AsText(bi.geom) AS wkt
            FROM bld_imputed bi
            LEFT JOIN pts_raw pts ON bi.id = pts.bld_id
            GROUP BY ALL
            """.replace("{self.release}", self.release).replace("{xmin}", str(xmin)).replace("{xmax}", str(xmax)).replace("{ymin}", str(ymin)).replace("{ymax}", str(ymax))

        return self.con.execute(query).fetchdf().to_dict('records')

    def calculate_nfa_by_category(self, building_type: str, amenity_list: list, total_nfa: float, num_floors: float = 1.0) -> dict:
        # 1. NORMALIZE the primary use
        b_type_lower = (building_type or "").lower()
        if any(k in b_type_lower for k in ["apartment-condo", "one-family-house", "multi-family-house","residential"]):
            primary_use = "Residential"
        else:
            primary_use = "Other"

        # 2. INITIALIZE fixed dictionary (matches your WEIGHT_MAP + Primary Use)
        nfa_dist = {cat: 0.0 for cat in self.INDUSTRY_MAP.keys()}
        if primary_use not in nfa_dist:
            nfa_dist[primary_use] = 0.0

        weighted_items = []

        # 3. DYNAMIC WEIGHTING: Scale primary use by floor count
        # Base weight (2.0) multiplied by floors ensures the 'body' of the building
        # dominates the NFA in high-rises.
        floors = max(float(num_floors or 1.0), 1.0)
        primary_weight = 2.0 * floors
        weighted_items.append({"cat": primary_use, "weight": primary_weight})

        # 4. ADD AMENITIES
        if amenity_list:
            for raw_cat in amenity_list:
                raw_cat_str = str(raw_cat).lower()
                matched_cat = None

                for main_cat, keywords in self.INDUSTRY_MAP.items():
                    if any(k in raw_cat_str for k in keywords):
                        matched_cat = main_cat
                        break

                target_cat = matched_cat if matched_cat else primary_use
                weight = self.WEIGHT_MAP.get(target_cat, 1.0)
                weighted_items.append({"cat": target_cat, "weight": weight})

        # 5. ALLOCATE
        total_weight = sum(item['weight'] for item in weighted_items)
        effective_nfa = max(total_nfa, 20.0 * (len(amenity_list) + 1)) if total_nfa <= 0 else total_nfa

        if total_weight > 0:
            for item in weighted_items:
                allocated = (item['weight'] / total_weight) * effective_nfa
                # Accumulate results and round to nearest 10 (scientific proxy signal)
                nfa_dist[item['cat']] = round(nfa_dist.get(item['cat'], 0.0) + allocated, -1)

        #check that no nulls etc..
        nfa_dist_out = {}
        for k, v in nfa_dist.items():
            if v is None or str(v).lower().strip() in ["null", "none"]:
                nfa_dist_out[k] = 0.0
            else:
                try:
                    nfa_dist_out[k] = max(0.0, float(v))
                except (ValueError, TypeError):
                    nfa_dist_out[k] = 0.0

        return nfa_dist_out

    def _reclassify_to_upd(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Refines raw building data into Urban Planning metrics.
        Includes GFA calculation and weighted NFA distribution for amenities.
        """

        # 1. Configuration for Filtering
        DROP_SUBTYPES = {'outbuilding', 'service', 'transportation'}
        DROP_CLASSES = {'garage', 'garages', 'parking', 'carport', 'roof'}

        b_class = str(record.get("class", "")).lower()
        b_subtype = str(record.get("subtype", "")).lower()

        if b_subtype in DROP_SUBTYPES or b_class in DROP_CLASSES:
            return None

        # 2. Reclassify Residential & Standard Types
        SUBTYPE_MAP = {
            "residential": "residential",
            "commercial": "commercial",
            "entertainment": "commercial",
            "education": "public",
            "religious": "public",
            "civic": "public",
            "medical": "public",
            "industrial": "industrial"
        }

        derived_type = SUBTYPE_MAP.get(b_subtype, "other")

        # Refine residential based on Class
        if b_class in {'house', 'bungalow', 'detached', 'cabin'}:
            derived_type = 'one-family-house'
        elif b_class in {'semi', 'semidetached_house', 'terrace'}:
            derived_type = 'multi-family-house'
        elif b_class in {'apartments', 'residential', 'dormitory'}:
            derived_type = 'apartment-condo'

        # 3. GFA/NFA Calculations
        num_floors = record.get("num_floors") or 1
        footprint = record.get("footprint_area_sqm", 0)
        gfa = footprint * num_floors
        total_nfa = gfa * 0.8  # Efficiency factor for Net Floor Area
        amenity_list = record.get("places", [])

        # 4. Weighted NFA Distribution
        nfa_dist = self.calculate_nfa_by_category(building_type=derived_type,
                                                  amenity_list=amenity_list,
                                                  total_nfa=total_nfa,
                                                  num_floors=num_floors
                                                  )

        # 5. Final UPD Output
        return {
            "id": record.get("id"),
            "building_type": derived_type,
            "num_floors": num_floors,
            "GFA": round(gfa, -1),
            "NFA_by_industry": nfa_dist,
            "wkt": record.get("wkt")
        }

    def run(self):
        """The standard execution entry point."""
        # 1. Fetch data (includes Imputation, Deduplication, and Clean Categories)
        raw_data = self._fetch_from_OMF(bbox=self.bbox)
        refined_data = []
        for r in raw_data:
            # clean the list to be truly empty if no amenities exist.
            r['places'] = [p for p in r.get('places', []) if p is not None]
            # ..apply Industry Mapping and other reclassification
            converted = self._reclassify_to_upd(r)
            if converted:
                refined_data.append(converted)

        return refined_data


# ----- Landcover Blueprint using OvertureMap Foundation (OMF) landuse & buildings -----
class OvertureMapLandcoverForBiodiversity:
    """
    Research Design: General landcover blueprint derived from OvertureMap Foundation.
    Utilizes a fast centroid-based spatial join to subtract building footprints from
    land-use parcels, dynamically generating enhanced landcover classes without heavy calculations.
    """

    def __init__(self, bbox, country_code):
        if duckdb is None:
            raise ModuleNotFoundError(
                "duckdb is required for OvertureMapLandcoverForBiodiversity. Install zzproxies[data]."
            )
        self.bbox = bbox
        self.country_code = country_code
        self.release = self._get_latest_release()
        self.con = duckdb.connect(':memory:')
        self.con.execute("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs;")

        # --- ECOLOGICAL RECLASSIFICATION & YARD RATIOS ---
        self.LANDCOVER_MAP = {
            "Vegetation_High": {"keywords": ["forest", "wood", "nature_reserve", "tree_canopy"], "weight": 1.0, "is_urban": False},
            "Vegetation_Low": {"keywords": ["grass", "meadow", "park", "garden", "pitch"], "weight": 0.7, "is_urban": False},
            "Wetland": {"keywords": ["wetland", "bog", "marsh", "swamp"], "weight": 1.0, "is_urban": False},
            "Water": {"keywords": ["water", "lake", "river", "pond"], "weight": 0.9, "is_urban": False},
            "Bare_Soil": {"keywords": ["sand", "bare_rock", "beach", "heath"], "weight": 0.4, "is_urban": False},
            "Agriculture": {"keywords": ["farmland", "farmyard", "orchard"], "weight": 0.5, "is_urban": False},

            # Urban Classes: These will trigger the Yard Splitter
            "Urban_Residential": {"keywords": ["residential"], "weight": 0.0, "is_urban": True},
            "Urban_Commercial": {"keywords": ["commercial", "retail", "cemetery"], "weight": 0.0, "is_urban": True},
            "Urban_Industrial": {"keywords": ["industrial", "construction", "brownfield", "parking", "highway"], "weight": 0.0, "is_urban": True},

            # Explicit Classes handled outside the dynamic loop
            "Building": {"weight": 0.0},
            "Managed_Yard": {"weight": 0.6}, # Permeable, planted (lawns, bushes)
            "Sealed_Yard": {"weight": 0.1}   # Impermeable (driveways, walkways, paved yards)
        }

        # If a polygon is 'Urban', how is the non-building area split?
        # Tuple: (Fraction_Managed, Fraction_Sealed)
        self.YARD_SPLIT_HEURISTICS = {
            "Urban_Residential": (0.70, 0.30),  # 70% green yard, 30% paved
            "Urban_Commercial": (0.15, 0.85),   # 15% landscaping, 85% parking/paved
            "Urban_Industrial": (0.05, 0.95),   # 5% landscaping, 95% hardstand
        }

    def _get_latest_release(self):
        url = "https://stac.overturemaps.org/catalog.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get("latest")

    def _fetch_from_OMF(self, bbox: List[float]):
        xmin, ymin, xmax, ymax = bbox

        geom_expr = """
            CASE
                WHEN regexp_matches(geometry::TEXT, '^(POLYGON|MULTIPOLYGON|POINT|LINESTRING).*') THEN ST_GeomFromText(geometry::TEXT)
                WHEN geometry::TEXT LIKE '{%"coordinates"%}' THEN ST_GeomFromGeoJSON(geometry::TEXT)
                ELSE ST_GeomFromText('GEOMETRYCOLLECTION EMPTY')
            END
        """

        # Uses a Point-in-Polygon (Centroid) join. Vastly faster than ST_Difference on polygons.
        query = f"""
            WITH bld AS (
                SELECT
                    id, 'building' AS raw_theme, subtype, class,
                    {geom_expr} AS geom,
                    ST_Area_Spheroid({geom_expr}) AS area_sqm,
                    ST_Centroid({geom_expr}) AS centroid
                FROM read_parquet('s3://overturemaps-us-west-2/release/{self.release}/theme=buildings/type=building/*')
                WHERE bbox.xmin > {xmin} AND bbox.xmax < {xmax} AND bbox.ymin > {ymin} AND bbox.ymax < {ymax}
            ),
            lu AS (
                SELECT
                    id, 'land_use' AS raw_theme, subtype, class,
                    {geom_expr} AS geom,
                    ST_Area_Spheroid({geom_expr}) AS area_sqm
                FROM read_parquet('s3://overturemaps-us-west-2/release/{self.release}/theme=base/type=land_use/*')
                WHERE bbox.xmin > {xmin} AND bbox.xmax < {xmax} AND bbox.ymin > {ymin} AND bbox.ymax < {ymax}
            ),
            wat AS (
                SELECT
                    id, 'water' AS raw_theme, subtype, class,
                    {geom_expr} AS geom,
                    ST_Area_Spheroid({geom_expr}) AS area_sqm
                FROM read_parquet('s3://overturemaps-us-west-2/release/{self.release}/theme=base/type=water/*')
                WHERE bbox.xmin > {xmin} AND bbox.xmax < {xmax} AND bbox.ymin > {ymin} AND bbox.ymax < {ymax}
            ),
            -- FAST SPATIAL JOIN: Sum building area per land_use parcel based on building centroid
            bld_in_lu AS (
                SELECT lu.id AS lu_id, SUM(b.area_sqm) AS contained_bld_area
                FROM bld b
                JOIN lu ON ST_Intersects(b.centroid, lu.geom)
                GROUP BY lu.id
            )

            -- 1. Output Buildings
            SELECT id, raw_theme, subtype, class, area_sqm, 0.0 AS contained_bld_area, ST_AsText(geom) AS wkt FROM bld
            UNION ALL
            -- 2. Output Water
            SELECT id, raw_theme, subtype, class, area_sqm, 0.0 AS contained_bld_area, ST_AsText(geom) AS wkt FROM wat
            UNION ALL
            -- 3. Output Land Use with aggregated building footprint area
            SELECT
                lu.id, lu.raw_theme, lu.subtype, lu.class, lu.area_sqm,
                COALESCE(bil.contained_bld_area, 0.0) AS contained_bld_area,
                ST_AsText(lu.geom) AS wkt
            FROM lu
            LEFT JOIN bld_in_lu bil ON lu.id = bil.lu_id
            WHERE lu.area_sqm > 0
            """.replace("{self.release}", self.release).replace("{xmin}", str(xmin)).replace("{xmax}", str(xmax)).replace("{ymin}", str(ymin)).replace("{ymax}", str(ymax))

        return self.con.execute(query).fetchdf().to_dict('records')

    def _reclassify_to_upd(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Refines raw map elements into biodiversity metrics.
        Returns a LIST of records, because one Urban Land Use parcel might
        split into multiple yard segments.
        """
        raw_theme = str(record.get("raw_theme", ""))
        subtype = str(record.get("subtype", "")).lower()
        b_class = str(record.get("class", "")).lower()
        total_area = record.get("area_sqm", 0)

        # Output container
        derived_records = []
        base_record = {
            "id": record.get("id"),
            "raw_overture_theme": raw_theme,
            "raw_subtype": subtype,
            "wkt": record.get("wkt")  # The parent geometry acts as the container
        }

        # --- 1. BUILDINGS & WATER (Pass-through) ---
        if raw_theme == "building":
            derived_records.append({**base_record, "landcover_class": "Building", "ecological_weight": self.LANDCOVER_MAP["Building"]["weight"], "area_sqm": round(total_area, 2), "ecological_area_sqm": 0.0})
            return derived_records

        elif raw_theme == "water":
            derived_records.append({**base_record, "landcover_class": "Water", "ecological_weight": self.LANDCOVER_MAP["Water"]["weight"], "area_sqm": round(total_area, 2), "ecological_area_sqm": round(total_area * self.LANDCOVER_MAP["Water"]["weight"], 2)})
            return derived_records

        # --- 2. LAND USE ---
        # Match class
        derived_lc_class = "Unclassified_Land"
        is_urban = False
        eco_weight = 0.2
        search_string = f"{subtype} {b_class}"

        for lc_key, lc_data in self.LANDCOVER_MAP.items():
            if "keywords" in lc_data and any(kw in search_string for kw in lc_data["keywords"]):
                derived_lc_class = lc_key
                eco_weight = lc_data["weight"]
                is_urban = lc_data.get("is_urban", False)
                break

        # Calculate Net Area (subtracting buildings)
        bld_area = record.get("contained_bld_area", 0)
        net_area = max(0.0, total_area - bld_area)

        if net_area <= 0:
            return derived_records # Parcel is entirely covered by buildings

        # --- 3. YARD SPLITTER LOGIC ---
        if is_urban and derived_lc_class in self.YARD_SPLIT_HEURISTICS:
            managed_ratio, sealed_ratio = self.YARD_SPLIT_HEURISTICS[derived_lc_class]

            # Managed Yard
            managed_area = net_area * managed_ratio
            if managed_area > 0:
                managed_w = self.LANDCOVER_MAP["Managed_Yard"]["weight"]
                derived_records.append({**base_record, "landcover_class": "Managed_Yard", "ecological_weight": managed_w, "area_sqm": round(managed_area, 2), "ecological_area_sqm": round(managed_area * managed_w, 2)})

            # Sealed Yard
            sealed_area = net_area * sealed_ratio
            if sealed_area > 0:
                sealed_w = self.LANDCOVER_MAP["Sealed_Yard"]["weight"]
                derived_records.append({**base_record, "landcover_class": "Sealed_Yard", "ecological_weight": sealed_w, "area_sqm": round(sealed_area, 2), "ecological_area_sqm": round(sealed_area * sealed_w, 2)})

        else:
            # Natural/Non-Urban land uses just get their base net area
            derived_records.append({**base_record, "landcover_class": derived_lc_class, "ecological_weight": eco_weight, "area_sqm": round(net_area, 2), "ecological_area_sqm": round(net_area * eco_weight, 2)})

        return derived_records

    def run(self):
        raw_data = self._fetch_from_OMF(bbox=self.bbox)
        refined_data = []

        for r in raw_data:
            # _reclassify_to_upd now returns a list of dictionaries
            converted_list = self._reclassify_to_upd(r)
            refined_data.extend(converted_list)

        return refined_data

# ----- Next Blueprint below here.. -----