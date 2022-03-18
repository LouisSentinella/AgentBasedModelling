import pickle
import random
import matplotlib
from mesa.space import MultiGrid, Grid, SingleGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
import numpy as np
import copy
from agents import *
import tracemalloc


class EvolutionModel(Model):
    """A model with some number of agents."""

    def __init__(self, n, width, height, max_age, mutation_rate, save_path="saved_models/uncategorized/model_"):
        self.snap = None
        self.num_agents = n
        #tracemalloc.start()
        self.n = n
        self.grid = SingleGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.running = True
        #self.snap = None
        self.mutation_rate = mutation_rate
        self.age = 0
        self.save_iterator = 10
        self.steps = 0
        self.max_age = max_age
        self.correct = 0
        self.weights = []
        self.count = 0
        self.winners = []
        self.vis_agents = self.generate_visual_agents()
        self.generate_agents(self.agent)
        self.datacollector = DataCollector(
            model_reporters={"Correct": correct_count})
        self.save_file_path = save_path
        # self.generate_agent_colours_from_gene_pool()
        for layer in self.net:
            for param in layer.parameters():
                param.requires_grad_(False)

    def step(self):
        self.steps += 1
        self.age += 1
        self.snap = None
        if (self.steps // self.max_age) % self.save_iterator == 0:
            with open(self.save_file_path + str(self.steps // self.max_age) + ".pkl", "wb") as f:
                pickle.dump(self, f)
        if self.age == self.max_age:
            #self.snap = tracemalloc.take_snapshot()
            self.weights = []
            self.correct = correct_amount(self)
            self.datacollector.collect(self)
            self.num_agents = 0
            self.schedule.step()
            self.sexual_reproduction()
            self.age = 0
            # self.generate_agent_colours_from_gene_pool()
            for idx, weight in enumerate(self.weights):
                if idx < (len(self.schedule.agents) - self.vis_agents):
                    self.schedule.agents[idx + self.vis_agents].weights = weight
            if self.num_agents < self.n:
                for i in range(self.num_agents, self.n):
                    self.num_agents += 1
                    self.schedule.agents[i + self.vis_agents].weights = random.choice(self.weights)
        else:
            self.schedule.step()

    def generate_agents(self, agent):
        # Create agents
        for i in range(self.vis_agents, self.n + self.vis_agents):
            a = agent(i, self)
            self.schedule.add(a)
            # Add the agent to a random grid cell
            new_pos = self.grid.find_empty()
            self.grid.place_agent(a, new_pos)

    def generate_agent_colours_from_gene_pool(self):
        vector = np.zeros_like(
            np.concatenate([x.cpu().numpy().flatten() for x in self.schedule.agents[self.vis_agents].weights]))
        similarities = []
        for agent in self.schedule.agents[self.vis_agents:]:
            vector += np.concatenate([x.cpu().numpy().flatten() for x in agent.weights])
            similarities.append(np.linalg.norm(vector))
            # result = 1 - spatial.distance.cosine(vector, agent.weights[0].flatten() + agent.weights[1].flatten() +
            # agent.weights[2].flatten() + agent.weights[3].flatten())
            # similarities.append(result)

        data = np.array(similarities).reshape(-1, 1)
        similarities = (data - np.min(data)) / (np.max(data) - np.min(data))
        for idx, agent in enumerate(self.schedule.agents[self.vis_agents:]):
            # Generate a color scale
            cmap = matplotlib.pyplot.cm.get_cmap('Spectral')
            # Select the color 75% of the way through the colorscale
            color = matplotlib.colors.rgb2hex(cmap(similarities[idx - self.vis_agents]))
            agent.colour = color

    def sexual_reproduction(self):
        # Generate pairs from agents
        with torch.no_grad():
            pairs = [[self.winners.pop(random.randint(0, len(self.winners) - 1)),
                      self.winners.pop(random.randint(0, len(self.winners) - 1))] for _ in
                     range(int(len(self.winners) // 2))]
            # Iterate through pairs
            for pair in pairs:
                # Add to weights
                for i in range(self.n // int(len(pairs))):
                    if self.num_agents % self.n != 0 or self.num_agents == 0:
                        new_weights = []
                        for j in range(len(pair[0].weights)):
                            new_weights.append(
                                torch.Tensor(np.array([pair[random.randint(0, 1)].weights[j].cpu().flatten()[x] for x in
                                                       range(len(pair[0].weights[j].flatten()))]).reshape(
                                    pair[0].weights[j].shape)))
                        self.num_agents += 1
                        if self.random.random() < self.mutation_rate:
                            section_to_mutate = new_weights[np.random.choice(range(len(new_weights)), 1,
                                                                             p=[0.8 / (len(new_weights) / 2),
                                                                                0.2 / (len(new_weights) / 2)] * int(
                                                                                 (len(new_weights) / 2)))[0]]
                            # print(section_to_mutate.shape)
                            bias_shapes = [new_weights[x].shape for x in range(1, len(new_weights), 2)]
                            if section_to_mutate.shape in bias_shapes:
                                randomRow = np.random.randint(section_to_mutate.shape[0], size=1)
                                section_to_mutate[randomRow] = np.random.randn()
                            else:
                                randomRow = np.random.randint(section_to_mutate.shape[0], size=1)
                                randomCol = np.random.randint(section_to_mutate.shape[1], size=1)
                                section_to_mutate[randomRow, randomCol] = np.random.randn()
                        self.weights.append(new_weights)

    def generate_visual_agents(self):
        return 0


class ComplexClassificationModel(EvolutionModel):
    def __init__(self, n, width, height, max_age, mutation_rate):
        self.net = torch.nn.Sequential(
            torch.nn.Linear(20, 10),
            torch.nn.ReLU(),
            torch.nn.Linear(10, 5)
        )
        self.agent = ComplexNeuralAgent

        super().__init__(n, width, height, max_age, mutation_rate)

    def is_correct(self, agent):
        if agent.pos[1] < self.grid.height // 5:
            if agent.pos[0] < self.grid.width // 2:
                return 1 == self.colour
            else:
                return 0 == self.colour
        else:
            return False

    def generate_visual_agents(self):
        colour_indicator_black = GridColour(0, self, "Black")
        self.grid.place_agent(colour_indicator_black, (37, 5))
        self.schedule.add(colour_indicator_black)
        colour_indicator_blue = GridColour(1, self, "Blue")
        self.grid.place_agent(colour_indicator_blue, (12, 5))
        self.schedule.add(colour_indicator_blue)
        colour_indicator_guess = GridColour(2, self, "Black" if self.colour == 0 else "Blue")
        self.grid.place_agent(colour_indicator_guess, (25, 30))
        self.schedule.add(colour_indicator_guess)

        return len(self.schedule.agents)


class SimpleClassificationModel(EvolutionModel):
    def __init__(self, n, width, height, max_age, mutation_rate):
        self.net = torch.nn.Sequential(
            torch.nn.Linear(4, 10),
            torch.nn.ReLU(),
            torch.nn.Linear(10, 5),
        )
        self.agent = SimpleNeuralAgent
        self.colour = 0
        super().__init__(n, width, height, max_age, mutation_rate)

    def is_correct(self, agent):
        if agent.pos[1] < self.grid.height // 5:
            if agent.pos[0] < self.grid.width // 2:
                return 1 == self.colour
            else:
                return 0 == self.colour
        else:
            return False

    def generate_visual_agents(self):
        colour_indicator_black = GridColour(0, self, "Black")
        self.grid.place_agent(colour_indicator_black, (37, 5))
        self.schedule.add(colour_indicator_black)
        colour_indicator_blue = GridColour(1, self, "Blue")
        self.grid.place_agent(colour_indicator_blue, (12, 5))
        self.schedule.add(colour_indicator_blue)
        colour_indicator_guess = GridColour(2, self, "Black" if self.colour == 0 else "Blue")
        self.grid.place_agent(colour_indicator_guess, (25, 30))
        self.schedule.add(colour_indicator_guess)

        return len(self.schedule.agents)


class SimplestClassificationModel(EvolutionModel):
    def __init__(self, n, width, height, max_age, mutation_rate):
        self.net = torch.nn.Sequential(
            torch.nn.Linear(2, 5),
        )
        self.colour = 0
        self.agent = SimpleNeuralAgent
        super().__init__(n, width, height, max_age, mutation_rate)

    def is_correct(self, agent):
        if agent.pos[1] < self.grid.height // 2:
            return 1 == self.colour
        else:
            return 0 == self.colour

    def generate_visual_agents(self):
        colour_indicator_black = GridColour(0, self, "Black")
        self.grid.place_agent(colour_indicator_black, (self.grid.width // 2, self.grid.height - 1))
        self.schedule.add(colour_indicator_black)
        colour_indicator_blue = GridColour(1, self, "Blue")
        self.grid.place_agent(colour_indicator_blue, (self.grid.width // 2, 0))
        self.schedule.add(colour_indicator_blue)
        colour_indicator_guess = GridColour(2, self, "Black" if self.colour == 0 else "Blue")
        self.grid.place_agent(colour_indicator_guess, (self.grid.width // 2, self.grid.height // 2))
        self.schedule.add(colour_indicator_guess)

        return len(self.schedule.agents)


class RaceClassificationModel(EvolutionModel):
    def __init__(self, n, width, height, max_age, mutation_rate, save_path="saved_models/uncategorized/model_"):
        self.net = torch.nn.Sequential(
            torch.nn.Linear(8, 6)
        )
        self.agent = RaceNeuralAgent
        super().__init__(n, width, height, max_age, mutation_rate, save_path)

    def is_correct(self, agent):
        if agent.pos[1] < self.grid.height // 4:
            return 1 == agent.colour
        elif agent.pos[1] > self.grid.height // 4:
            return 0 == agent.colour
        else:
            return False

    def sexual_reproduction(self):
        super().sexual_reproduction()
        for agent in self.schedule.agents:
            agent.colour = random.randint(0, 1)


class FourRaceClassificationModel(EvolutionModel):
    def __init__(self, n, width, height, max_age, mutation_rate, save_path="saved_models/uncategorized/model_"):
        self.net = torch.nn.Sequential(
            torch.nn.Linear(8, 10),
            torch.nn.ReLU(),
            torch.nn.Linear(10,6)
        )
        self.agent = FourRaceNeuralAgent
        super().__init__(n, width, height, max_age, mutation_rate, save_path)

    def is_correct(self, agent):
        if agent.pos[1] < self.grid.height // 4:
            if agent.pos[0] < self.grid.width // 2:
                return 0 == agent.colour
            else:
                return 1 == agent.colour
        elif agent.pos[1] > self.grid.height // 4:
            if agent.pos[0] < self.grid.width // 2:
                return 2 == agent.colour
            else:
                return 3 == agent.colour
        else:
            return False

    def sexual_reproduction(self):
        super().sexual_reproduction()
        for agent in self.schedule.agents:
            agent.colour = random.randint(0, 3)


class SimpleDownModel(EvolutionModel):
    def __init__(self, n, width, height, max_age, mutation_rate):
        self.net = torch.nn.Sequential(
            torch.nn.Linear(3, 5)
        )
        self.agent = SimpleNeuralAgent

        super().__init__(n, width, height, max_age, mutation_rate)

    def is_correct(self, agent):
        if agent.pos[1] < self.grid.height // 5:
            return True
        else:
            return False


def correct_amount(model):
    return len([x for x in model.schedule.agents if model.is_correct(x)])


def correct_count(model):
    if model.steps % model.max_age == 0:
        model.count = (len([x for x in model.schedule.agents if model.is_correct(x)]) / len(
            model.schedule.agents)) * 100
    return model.count
