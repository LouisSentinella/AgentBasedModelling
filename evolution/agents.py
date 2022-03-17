import copy

from mesa import Model, Agent
import torch
import tracemalloc

device = torch.device("cuda:0")


class NeuralAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

        self.type = "Neural"

    def step(self):
        # The agent's step will go here
        if self.model.age == self.model.max_age:

            if self.model.is_correct(self):
                self.model.winners.append(self)
            self.die()
        else:
            self.choose_action()

    def choose_action(self):
        inputs = self.get_inputs()

        for i in range(int(len(self.weights) / 2)):
            self.model.net[2 * i].weight = torch.nn.Parameter(self.weights[2 * i])
            self.model.net[2 * i].bias = torch.nn.Parameter(self.weights[(2 * i) + 1])

        with torch.no_grad():
            outputs = self.model.net(torch.tensor(inputs, dtype=torch.float))

        im_neighborhood = self.generate_neighborhood_pad()

        with torch.no_grad():
            move = torch.argmax(outputs)
        im_neighborhood.append(self.random.choice(im_neighborhood))
        if self.model.grid.is_cell_empty(im_neighborhood[move]):
            self.model.grid.move_agent(self, im_neighborhood[move])
        else:
            self.model.grid.move_agent(self, self.pos)

    def die(self):
        self.model.grid.move_to_empty(self)

    def generate_neighborhood_pad(self):
        neighborhood = []
        if self.pos[0] == 0 and self.pos[1] == 0:
            neighborhood = [self.pos, self.pos, self.pos, (self.pos[0], self.pos[1] + 1),
                                      (self.pos[0] + 1, self.pos[1])]
        elif self.pos[0] == 0 and self.pos[1] == self.model.grid.height - 1:
            neighborhood = [self.pos, (self.pos[0], self.pos[1] - 1), self.pos, self.pos,
                                      (self.pos[0] + 1, self.pos[1])]
        elif self.pos[0] == 0:
            neighborhood = [self.pos, (self.pos[0], self.pos[1] - 1), self.pos,
                                      (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1])]
        elif self.pos[0] == self.model.grid.width - 1 and self.pos[1] == 0:
            neighborhood = [(self.pos[0] - 1, self.pos[1]), self.pos, self.pos,
                                      (self.pos[0], self.pos[1] + 1), self.pos]
        elif self.pos[0] == self.model.grid.width - 1 and self.pos[1] == self.model.grid.height - 1:
            neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      self.pos, self.pos]
        elif self.pos[0] == self.model.grid.width - 1:
            neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      (self.pos[0], self.pos[1] + 1), self.pos]
        elif self.pos[1] == 0:
            neighborhood = [(self.pos[0] - 1, self.pos[1]), self.pos, self.pos,
                                      (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1])]
        elif self.pos[1] == self.model.grid.height - 1:
            neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      self.pos, (self.pos[0] + 1, self.pos[1])]
        else:
            neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1])]

        return neighborhood

class ComplexNeuralAgent(NeuralAgent):
    def __init__(self, model, pos):
        super().__init__(model, pos)
        self.weights = [torch.randn_like(self.model.net[0].weight), torch.randn_like(self.model.net[0].bias),
                        torch.randn_like(self.model.net[2].weight), torch.randn_like(self.model.net[2].bias)]
        self.model.weights.append(self.weights)

    def get_inputs(self):
        neighbours = [(x, self.pos[1]) for x in range(self.pos[0] - 4, self.pos[0] + 5)] + [(self.pos[0], y) for y in
                                                                                            range(self.pos[1] - 4,
                                                                                                  self.pos[1] + 5)]
        neighbours.remove(self.pos)
        neighbours.remove(self.pos)
        return [self.model.age, self.model.colour] + [self.model.grid.is_cell_empty(pos) if (
                0 <= pos[0] < self.model.grid.width and 0 <= pos[1] < self.model.grid.height) else 2 for pos in
                                                      neighbours] + list(self.pos)


class SimpleNeuralAgent(NeuralAgent):
    def __init__(self, model, pos):
        super().__init__(model, pos)
        self.colour = "Black"
        self.type = "Simple"
        self.weights = [torch.randn_like(self.model.net[0].weight), torch.randn_like(self.model.net[0].bias)]
        self.model.weights.append(self.weights)

    def get_inputs(self):
        return [self.model.age / self.model.max_age] + [self.pos[0] / (self.model.grid.width - 1),
                                                        self.pos[1] / (self.model.grid.height - 1)]


class RaceNeuralAgent(NeuralAgent):
    def __init__(self, model, pos):
        super().__init__(model, pos)
        self.weights = [torch.randn_like(self.model.net[0].weight), torch.randn_like(self.model.net[0].bias)]
        self.colour = self.random.randint(0, 1)
        self.type = "Race"
        self.model.weights.append(self.weights)

    def get_inputs(self):
        ate_neighborhood = self.generate_neighborhood_pad()
        ate_neighborhood.pop(2)
        for idx, x in enumerate(ate_neighborhood):
            if x == self.pos:
                ate_neighborhood[idx] = 1
            elif self.model.grid.is_cell_empty(x):
                ate_neighborhood[idx] = 2/3
            else:
                ate_neighborhood[idx] = 1/3
        return [self.model.age / self.model.max_age, 0.7 if (self.colour == 1) else 0.3] + [
            self.pos[0] / (self.model.grid.width - 1), self.pos[1] / (self.model.grid.height - 1)] + ate_neighborhood


class FourRaceNeuralAgent(NeuralAgent):
    def __init__(self, model, pos):
        super().__init__(model, pos)
        self.weights = [torch.randn_like(self.model.net[0].weight), torch.randn_like(self.model.net[0].bias),torch.randn_like(self.model.net[2].weight), torch.randn_like(self.model.net[2].bias)]
        self.colour = self.random.randint(0, 3)
        self.type = "Race"
        self.model.weights.append(self.weights)

    def get_inputs(self):
        ate_neighborhood = self.generate_neighborhood_pad()
        ate_neighborhood.pop(2)
        for idx, x in enumerate(ate_neighborhood):
            if x == self.pos:
                ate_neighborhood[idx] = 1
            elif self.model.grid.is_cell_empty(x):
                ate_neighborhood[idx] = 2/3
            else:
                ate_neighborhood[idx] = 1/3
        return [self.model.age / self.model.max_age, (self.colour + 1)/4] + [
            self.pos[0] / (self.model.grid.width - 1), self.pos[1] / (self.model.grid.height - 1)] + ate_neighborhood


class GridColour(Agent):
    def __init__(self, unique_id, model, colour):
        super().__init__(unique_id, model)
        self.colour = colour
        self.type = "GridColour"

    def step(self):
        # The agent's step will go here
        self.model.grid.move_agent(self, self.pos)
