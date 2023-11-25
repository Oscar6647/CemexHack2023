#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from math import radians, sin, cos, sqrt, atan2
from flask import Flask
app = Flask(__name__)


# In[ ]:


def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Radius of Earth in kilometers (mean value)
    R = 6371

    # Calculate the distance
    dist = round(R * c, 0)
    distance = int(dist)

    return distance


# In[ ]:


def create_distance_matrix(locations):
    num_locations = len(locations)
    distance_matrix = [[0] * num_locations for _ in range(num_locations)]

    for i in range(num_locations):
        for j in range(i + 1, num_locations):
            lat1, lon1 = locations[i]
            lat2, lon2 = locations[j]
            distance = haversine(lat1, lon1, lat2, lon2)
            distance_matrix[i][j] = distance
            distance_matrix[j][i] = distance

    return distance_matrix


# In[ ]:


def create_data_model(locations, vehicles):
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = create_distance_matrix(locations)
    data["num_vehicles"] = vehicles
    data["depot"] = 0
    return data


# In[ ]:


def solucion(data, manager, routing, solution):
    """Returns the solution as well as printing it on console."""
    max_route_distance = 0
    all_routes = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_nodes = []  # List to store nodes visited by the current vehicle
        route_distance = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_nodes.append(node)

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)

        node = manager.IndexToNode(index)
        route_nodes.append(node)

        # Add the current route to the list of all routes
        all_routes.append(route_nodes)

        # Print information about the current route
        print(f"Recorrido para el vehiculo {vehicle_id}:")
        print(" -> ".join(map(str, route_nodes)))
        print(f"Distance of the route: {route_distance}m\n")

        max_route_distance = max(route_distance, max_route_distance)

    print(f"Maximum of the route distances: {max_route_distance}m")

    return all_routes


# In[ ]:


def main():
    """Entry point of the program."""
    # Get input for the number of places and their coordinates
    num_places = int(input("Ingresa el numero de lugares: "))
    num_vehicles = int(input("Ingresa el numero de vehiculos: "))
    locations = []

    for i in range(num_places):
        lat = float(input(f"Latitude  {i + 1}: "))
        lon = float(input(f"Longitude {i + 1}: "))
        locations.append((lat, lon))

    # Instantiate the data problem.
    data = create_data_model(locations, num_vehicles)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,  
        3000,  
        True,  
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console and return all_routes.
    if solution:
        all_routes = solucion(data, manager, routing, solution)
        # Now you can use the 'all_routes' variable in the rest of your code.
        print("All Routes:", all_routes)
    else:
        print("No solution found !")

    #solution array with latitude and longitudes 
    solution_array = []
    for route in all_routes:
        route_array = []
        for node in route:
            route_array.append(locations[node])
        solution_array.append(route_array)
    print("Solution Array:", solution_array)

    @app.route('/solution', methods=['POST'])
    def solution():
        return str(solution_array)
    
    #with get request latitude and longitude 
    
    
if __name__ == "__main__":
    main()

