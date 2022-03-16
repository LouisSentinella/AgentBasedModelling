from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from models import *


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true"}

    if agent.type == "mean":
        portrayal["Color"] = "red"
    elif agent.type == "altruistic":
        portrayal["Color"] = "blue"
    elif agent.type == "greenbeard":
        portrayal["Color"] = "green"
    elif agent.type == "spiteful_family":
        portrayal["Color"] = "purple"
    elif agent.type == "spiteful":
        portrayal["Color"] = "#C8A2C8"
    elif agent.type == "tft":
        portrayal["Color"] = "orange"
    elif agent.type == "tft_family":
        portrayal["Color"] = "yellow"
    else:
        portrayal["Color"] = "grey"

    if agent.age < 18:
        portrayal["r"] = 0.3
        portrayal["Layer"] = 1
        portrayal["Color"] = "pink"
    else:
        portrayal["r"] = 0.8
        portrayal["Layer"] = 0
    return portrayal


chart = ChartModule([{"Label": "Meanies",
                      "Color": "Red"}, {"Label": "GreenBeards",
                                        "Color": "Green"}, {"Label": "Altruistic",
                                                            "Color": "Blue"}, {"Label": "Imposters",
                                                                               "Color": "Grey"},
                     {"Label": "Spiteful", "Color": "#C8A2C8"}, {"Label": "Spiteful Family", "Color" : "Purple"}, {"Label": "TFT", "Color": "Orange"},
                     {"Label": "TFT Family", "Color": "Yellow"}],
                    data_collector_name='datacollector')
chart_score = ChartModule([{"Label": "Average Score", "Color": "Black"}], data_collector_name='datacollector')
chart_age = ChartModule([{"Label": "Average Age", "Color": "Black"}], data_collector_name='datacollector')

chart_pop = ChartModule(
    [{"Label": "Total", "Color": "Blue"}, {"Label": "Widows", "Color": "Black"},
     {"Label": "Kids", "Color": "Pink"}, {"Label": "Married", "Color": "Red"}, {"Label": "Virgins", "Color": "Green"}], data_collector_name='datacollector')
grid = CanvasGrid(agent_portrayal, 50, 50, 500, 500)
server = ModularServer(GameModel, [grid, chart, chart_score, chart_pop, chart_age], "Game Model",
                       {"N": 600, "width": 50, "height": 50, "harshness": 0.7})
server.port = 8521
server.launch()
