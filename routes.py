#!/usr/bin/env python
# coding: utf-8

import json
from flask import Flask, request
app = Flask(__name__)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from math import radians, sin, cos, sqrt, atan2


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


def create_data_model(locations, vehicles):
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = create_distance_matrix(locations)
    data["num_vehicles"] = vehicles
    data["depot"] = 0
    return data


def solucion(data, manager, routing, solution):
    """Returns the solution as well as printing it on the console."""
    max_route_distance = 0
    all_routes = []
    litros_total = 0
    costo_total = 0

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route_nodes = []  # List to store nodes visited by the current vehicle
        route_distance = 0
        route_actual = 0
        litros_gas = 0
        litros_actual = 0
        costo = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_nodes.append(node)

            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += (routing.GetArcCostForVehicle(previous_index, index, vehicle_id))
            route_actual = (routing.GetArcCostForVehicle(previous_index, index, vehicle_id))
            litros_gas += round(route_actual * 0.35,1)  # se gastan 35 litros por cada 100 km
            litros_actual = round(route_actual * 0.35,1)
            costo += round(litros_actual * 22.76,1)

        node = manager.IndexToNode(index)
        route_nodes.append(node)

        # Add the current route to the list of all routes
        all_routes.append(route_nodes)

        # Print information about the current route
        print(f"Recorrido para el vehiculo {vehicle_id}:")
        print(" -> ".join(map(str, route_nodes)))
        print(f"Distance of the route: {route_distance} km")
        print(f"Litros Gastados: {litros_gas} lts")
        print(f"Costo: ${costo}\n")

        max_route_distance = max(route_distance, max_route_distance)
        litros_total += round(litros_gas, 2)
        costo_total += round(costo, 2)

    print("----------------------------------------------")
    print("TOTALES:")
    print(f"Maxima distancia: {max_route_distance} km")
    print(f"Litros gastados totales: {litros_total} lts")
    print(f"Costo Total: ${costo_total}")

    return all_routes, max_route_distance, litros_gas, costo_total

# locations: array of tupples, indicating (lat, lon)
def invoke_model(num_vehicles, locations):
    """Entry point of the program."""

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
        all_routes, max_route_distance, litros_gas, costo_total = solucion(data, manager, routing, solution)
        # Now you can use the 'all_routes' variable in the rest of your code.
        print("All Routes:", all_routes)
    else:
        return "No solution"


    if solution:
        solution_array = []
        for route in all_routes:
            route_array = []
            for node in route:
                route_array.append(locations[node])
            solution_array.append(route_array)

        print("Solution Array:", solution_array)

        return solution_array, max_route_distance, litros_gas, costo_total


"""
Body format:
{
    "positions": [  {"lat": 16, "lng": 20}, {"lat": 14, "lng": 20}, {"lat": 10, "lng": 20}]
}
"""
@app.route('/solution', methods=['POST'])
def solution():
    try:
        obj = json.loads(request.data) 
        # print("OBJECT:")
        # print(obj)
        positions = obj['positions']
        print(positions)

        # locations = [(10, 20), (11, 21), (11.5, 22)]
        locations = []
        num_vehicles = 2
        
        for pos in positions:
            print("pos:", pos)
            if ('lat' in pos and 'lng' in pos):
                locations.append((pos['lat'], pos['lng']))
            else:
                print("WARNING: missing property in location")
        
        if (len(locations) < 2):
            return "Error: not enough location."
        
        result = invoke_model(num_vehicles, locations)
        print(result)
        print(type(result))

        if (isinstance(result, str)):
            return json.dumps(result)
        elif (isinstance(result, tuple)):
            
            solution_array, max_route_distance, litros_total, costo_total = result
            
            response_data = {
                "solution_array": solution_array,
                "max_route_distance": max_route_distance,
                "litros_total": litros_total,
                "costo_total": costo_total
            }
            return json.dumps(response_data)
        else:
            return "Error: unhandled result of invoking model."

        
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON data"}), 400, {'Content-Type': 'application/json'}


