import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

# Load traffic data from CSV
traffic_csv = "Farmington_Traffic.csv"
traffic_data = pd.read_csv(traffic_csv)

# Normalize road names for better matching
traffic_data["Road Name"] = traffic_data["Road Name"].str.lower()
congestion_weights = {"Low": 1, "Medium": 1.5, "High": 2}

# User selects travel mode (fixing input issues)
mode = input("Select travel mode (walking/driving): ").strip().lower()  # Remove spaces and normalize case
travel_modes = {'walking': 'walk', 'driving': 'drive'}
if mode not in travel_modes:
    print("Invalid mode selected. Please type 'walking' or 'driving'.")
    exit()

# Load graph for Farmington, NM
try:
    G = ox.graph_from_place("Farmington, NM", network_type=travel_modes[mode])
except Exception as e:
    print(f"Error loading map data: {e}")
    exit()

# Ensure the graph is not empty
if not G or len(G.nodes) == 0:
    print("Error: The graph G is empty. Check city name or internet connection.")
    exit()

# Convert traffic data into a GeoDataFrame for spatial operations
gdf_traffic = gpd.GeoDataFrame(
    traffic_data, geometry=gpd.points_from_xy(traffic_data.Longitude, traffic_data.Latitude))

# Function to adjust road weights based on congestion
def apply_congestion_weights(G, gdf_traffic):
    for u, v, data in G.edges(data=True):
        if "geometry" in data:
            road_geom = data["geometry"]
            for _, row in gdf_traffic.iterrows():
                if road_geom.intersects(row.geometry):  # Check if road overlaps with known traffic areas
                    congestion_level = row["Congestion Level"]
                    weight_multiplier = congestion_weights.get(congestion_level, 1)
                    if "length" in data:
                        data["length"] *= weight_multiplier
    return G

# Apply congestion weighting
G = apply_congestion_weights(G, gdf_traffic)

while True:
    # Get user input for locations
    start_location = input("Enter start location: ")
    end_location = input("Enter destination: ")
    
    try:
        # Convert locations to nearest graph nodes
        start_node = ox.distance.nearest_nodes(G, *ox.geocode(start_location)[::-1])
        end_node = ox.distance.nearest_nodes(G, *ox.geocode(end_location)[::-1])
    except Exception as e:
        print(f"Error finding locations: {e}")
        continue

    try:
        # Compute shortest path considering congestion weights
        route = nx.shortest_path(G, start_node, end_node, weight="length")
    except nx.NetworkXNoPath:
        print("No available path between the selected locations.")
        continue
    
    # Plot the graph and route
    fig, ax = plt.subplots(figsize=(10, 10))
    ox.plot_graph(G, ax=ax, node_color='gray', edge_color='lightgray', show=False, close=False)
    
    # Draw the computed route in blue
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
        x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
        ax.plot([x1, x2], [y1, y2], color='blue', linewidth=2, label='Optimized Route')
    
    plt.title("Optimized Route Considering Traffic")
    plt.legend()
    plt.show()
    
    # Ask if user wants to recalculate with different constraints
    rerun = input("Do you want to find a new route? (yes/no): ").lower()
    if rerun != "yes":
        break
