import os
import sys
import urllib
import json
import time
import pandas as pd
import valhalla

def read_gps_data(data_path):
    with open(data_path) as f:

        # skip header
        f.readline()
        coords = []

        for line in f:
            coord = line.strip().split('\t')[2:]
            coords.append([float(elem) for elem in coord])

    return coords
    
def create_query(coords, costing="auto", shape_match="walk_or_snap"):

    filters = {"attributes": ["matched.point",
                              "matched.type",
                              "matched.edge_index",
                              "matched.distance_along_edge",
                              "matched.distance_from_trace_point"],
               "action": "include"}

    query = {}
    query["costing"] = costing
    query["shape_match"] = shape_match
    query["filters"] = filters

    query["shape"] = [{"lat": pt[0], "lon": pt[1]} for pt in coords]

    return query
    
def make_valhalla_mapmatch_query(coords):
    
    start = time.time()
    
    query = json.dumps(create_query(coords))
    valhalla.Configure('./valhalla.json')
    actor = valhalla.Actor()
    response = actor.TraceAttributes(query)
    matched = json.loads(response)
    
    print("Time taken for Map Matching : %.3f" % (time.time() - start))

    return matched

def parse_response(matched):
    
    columns = ["mm_lon", "mm_lat", "edge_id", "pos", "dev", "type"]
    
    matched_trip = []
    n_matched = 0
    n_pts = 0
    
    for pt in matched["matched_points"]:
        
        n_pts += 1
        if pt["type"] == "unmatched":
            continue
        
        matched_trip.append([pt["lon"], 
                             pt["lat"],
                             pt["edge_index"],
                             pt["distance_along_edge"],
                             pt["distance_from_trace_point"],
                             pt["type"]])            
        n_matched += 1

    print("Map Matching Accuracy : %.2f" % (n_matched / n_pts))
    
    return pd.DataFrame(matched_trip, columns=columns)
    
if __name__ == "__main__":

    # loading GPS data
    data_path = "data/gps_data.txt"
    coords = read_gps_data(data_path)
    
    matched = make_valhalla_mapmatch_query(coords)
    
    parsed_df = parse_response(matched)
    
    parsed_df.to_csv("results/processed.csv")
