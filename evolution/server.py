from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from models import *


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true", "Layer": 0, "Color": "red", "r": 0.5}
    if agent.type == "GridColour":
        portrayal["Color"] = agent.colour
        portrayal["Shape"] = "rect"
        portrayal["Filled"] = "true"
        portrayal["w"] = 1
        portrayal["h"] = 1
        portrayal["Layer"] = 1
    elif agent.type == "Race":
        colour_dict = {0: "Black", 1:"Blue", 2:"Red", 3:"Green"}
        portrayal["Color"] = colour_dict[agent.colour]

    elif agent.type == "Simple":
        portrayal["Color"] = agent.colour

    return portrayal


if __name__ == "__main__":
    chart_score = ChartModule([{"Label": "Correct", "Color": "Black"}], data_collector_name='datacollector')
    grid = CanvasGrid(agent_portrayal, 35, 35, 700, 700)
    server = ModularServer(FourRaceClassificationModel, [grid, chart_score], "Game Model",
                           {"n": 100, "width": 35, "height": 35, "mutation_rate": 0.1, "max_age": 200, "save_path": "saved_models/four_race/race_evolution_"})
    server.port = 8521
    server.launch()
