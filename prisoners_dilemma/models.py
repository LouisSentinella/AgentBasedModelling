from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa import Model
import numpy as np
import random
from agents import *


class GameModel(Model):
    """A model with some number of agents."""

    def __init__(self, N, width, height, harshness=1):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.running = True
        self.time_list = ["morning", "midday", "afternoon", "evening", "night"]
        self.time_index = 0
        self.time = self.time_list[self.time_index]
        self.out_agents = []
        self.out_minglers = []
        self.harshness = harshness
        x_01n1n2_y = [(0, y) for y in range(height)] + [(1, y) for y in range(height)] + [(width - 2, y) for y in
                                                                                          range(height)] + [
                         (width - 1, y) for y in range(height)]
        y_01n1n2_x = [(x, 0) for x in range(2, width - 2)] + [(x, 1) for x in range(2, width - 2)] + [(x, height - 2)
                                                                                                      for x in range(2,
                                                                                                                     width - 2)] + [
                         (x, height - 1) for x in range(2, width - 2)]
        self.unoccupied_houses = x_01n1n2_y + y_01n1n2_x
        self.occupied_houses = []
        #print(self.unoccupied_houses)
        # Create agents
        for i in range(self.num_agents):
            selection = np.random.choice(
                [MeanAgent, AltruisticAgent, GreanBeardAltruistic, ImposterGreenBeards, SpitefulFamily,
                 Spiteful, TitForTat, TitForTatFamily], 1, p=[1/6]*2 + [0, 0] + [1/6]*4)[0]
            a = selection(i, self)
            self.schedule.add(a)

        # Randomly generate couples, and set homes
        agents = [agent for agent in self.schedule.agents]

        for i in range(self.num_agents // 2):
            a = agents.pop(random.randint(0, len(agents) - 1))
            b = agents.pop(random.randint(0, len(agents) - 1))
            a.spouse = b
            b.spouse = a
            a.parents = []
            b.parents = []
            a.age = np.random.choice(
                [random.randint(18, 30), random.randint(30, 45), random.randint(45, 60), random.randint(60, 85)], 1,
                p=[0.3, 0.3, 0.3, 0.1])[0]
            b.age = random.randint(a.age - 5, a.age + 5)
            # Choose home location from edge of grid
            a.home_cell = random.choice(self.unoccupied_houses)
            self.unoccupied_houses.remove(a.home_cell)
            self.occupied_houses.append(a.home_cell)
            b.home_cell = a.home_cell
            self.grid.place_agent(a, a.home_cell)
            self.grid.place_agent(b, b.home_cell)

        agents = [agent for agent in self.schedule.agents]
        # Randomly generate kids
        type_dict = {"mean": MeanAgent, "altruistic": AltruisticAgent, "greenbeard": GreanBeardAltruistic,
                     "imposter": ImposterGreenBeards, "spiteful_family": SpitefulFamily, "spiteful": Spiteful, "tft": TitForTat,
                     "tft_family": TitForTatFamily}
        for i in range(len(agents) // 2):
            a = agents.pop(random.randint(0, len(agents) - 1))
            agents.remove(a.spouse)
            if 18 <= a.age <= 55 and 18 <= a.spouse.age <= 55:
                child_type = random.choice([a.type, a.spouse.type])
                if random.random() < 0.5:
                    self.num_agents += 1
                    child = type_dict[child_type](self.num_agents, self)
                    child.home_cell = a.home_cell
                    self.schedule.add(child)
                    self.grid.place_agent(child, child.home_cell)
                    a.children.append(child)
                    a.spouse.children.append(child)
                    child.age = random.randint(0, min(a.age, a.spouse.age) - 18)
                    child.parents = [a, a.spouse]
                    # child.pos = child.home_cell

        self.datacollector = DataCollector(
            model_reporters={"Meanies": count_meanies, "Altruistic": count_altruistics,
                             "GreenBeards": count_greenbeards, "Imposters": count_imposters, "Total": count_total,
                             "Average Score": average_score, "Virgins": count_virgins, "Kids": count_kids,
                             "Married": count_married, "Average Age": average_age,
                             "Spiteful": count_spiteful, "Spiteful Family": count_spiteful_family, "TFT": count_tit_for_tat,
                             "TFT Family": count_tit_for_tat_family, "Widows": count_widows}
        )

    def step(self):
        self.schedule.step()
        self.time_index = (self.time_index + 1) % len(self.time_list)
        self.time = self.time_list[self.time_index]
        if self.time == "night":
            self.out_agents = []
        self.datacollector.collect(self)



def count_greenbeards(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "greenbeard")


def count_tit_for_tat(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "tft")


def count_tit_for_tat_family(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "tft_family")


def count_meanies(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "mean")


def count_altruistics(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "altruistic")


def count_imposters(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "imposter")


def count_spiteful(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "spiteful")


def count_spiteful_family(model):
    return sum(1 for agent in model.schedule.agents if agent.type == "spiteful_family")


def count_total(model):
    return sum(1 for _ in model.schedule.agents)


def average_score(model):
    return sum(agent.score for agent in model.schedule.agents) / len(model.schedule.agents)


def average_age(model):
    return sum(agent.age for agent in model.schedule.agents) / len(model.schedule.agents)


def count_virgins(model):
    return sum(1 for agent in model.schedule.agents if not agent.spouse and not agent.dead_spouse and agent.age >= 18)


def count_kids(model):
    return sum(1 for agent in model.schedule.agents if agent.age < 18)


def count_married(model):
    return sum(1 for agent in model.schedule.agents if agent.spouse)


def count_widows(model):
    return sum(1 for agent in model.schedule.agents if not agent.spouse and agent.dead_spouse)
