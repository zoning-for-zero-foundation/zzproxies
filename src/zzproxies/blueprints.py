# src/zzproxies/blueprints.py

"""
Class functions to generate UPD blueprints from public data sources for defined zzproxies.
Each blueprint class should have:
- __init__(self, bbox, country_code): to set up the bounding box and country code
- run(self): to execute the data fetching and processing, returning UPD-formatted data
- naming convention: Name of Blueprint indicating source followed by version as MONTHYEAR
  (e.g., OverturemapBuildingsWithPlaces_vDEC2025)
- Class-related special library imports should be included within the particular function in the class
  (to be imported only when the function is called) but generally avoid this.
"""

#general imports for blueprints to share
import duckdb #we encourage duckdb for in-memory spatial queries
from typing import List, Dict, Any, Optional


# ----- Blueprint using OvertureMap Foundation (OMF) buildings and places -----
class OvertureMapBuildingsWithPlaces_vDEC2025:
    """
    Research Design: Building level UPD derived from OvertureMap Foundation: https://docs.overturemaps.org 
    Self-contained helpers for OvertureMap Foundation URL-sources and spatial joins.
    """

    def __init__(self, bbox, country_code):
        self.bbox = bbox
        self.country_code = country_code
        self.release = "2025-12-17.0"  #https://docs.overturemaps.org/release-calendar/
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
                "Leisure & Culture": 1.2,
                "Industry & Services": 2.2,
                "Transport": 0.4,
                "Other": 1.0
            }


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
                    COALESCE(categories, 'other') as category,
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

# ----- Next Blueprint below here.. -----