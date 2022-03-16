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
        portrayal["Color"] = "Black" if agent.colour == 1 else "Blue"
    elif agent.type == "Simple":
        portrayal["Color"] = agent.colour

    return portrayal


if __name__ == "__main__":
    chart_score = ChartModule([{"Label": "Correct", "Color": "Black"}], data_collector_name='datacollector')
    grid = CanvasGrid(agent_portrayal, 50, 50, 750, 750)
    server = ModularServer(RaceClassificationModel, [grid, chart_score], "Game Model",
                           {"n": 200, "width": 50, "height": 50, "mutation_rate": 0.005, "max_age": 100})
    server.port = 8521
    server.launch()
