from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from models import *


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true", "Layer": 0, "Color": "red", "r": 0.5}
    if agent.type == "Masked":
        portrayal["Color"] = "Orange"
    elif agent.type == "Quarantined":
        portrayal["Color"] = "Purple"
    elif agent.type == "Unmasked":
        portrayal["Color"] = "Red"
    elif agent.type == "Infected":
        portrayal["Color"] = "Green"
        portrayal["Layer"] = 1
    return portrayal


if __name__ == "__main__":
    chart_score = ChartModule([{"Label": "Infected", "Color": "Green"}, {"Label": "Dead", "Color": "Black"}, {"Label": "Alive", "Color": "Red"}, {"Label" : "Uninfected", "Color" : "Orange"}], data_collector_name='datacollector')
    chart_inf_dead = ChartModule([{"Label": "Infected", "Color": "Green"}, {"Label": "Dead", "Color": "Black"}], data_collector_name='datacollector')
    grid = CanvasGrid(agent_portrayal, 50, 50, 700, 700)
    server = ModularServer(PandemicModel, [grid, chart_score, chart_inf_dead], "Pandemic Model",
                           {"n": 400, "width": 50, "height": 50, "masked_percentage" : 0.30 , "asymptomatic_probability":0.2, "infection_length" : 10  , "infection_probability" : 0.12  , "time_till_symptoms" : 5 , "quarantine_length" : 14 , "immunity_length" : 120 , "n_workplaces" : 25 , "n_shops" : 5 , "n_schools" : 2 , "n_churches" : 2, "n_couples" : 150, "couples_with_kids_percentage" : 0.7, "initial_infected_percentage" : 0.005, "house_depth":4, "lockdown_threshold" : 0.01, "liftlockdown_threshold" : 0.005})
    server.port = 8521
    server.launch()
