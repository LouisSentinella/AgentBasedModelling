from mesa import Model, Agent
import torch

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
        with torch.no_grad():
            for i in range(int(len(self.weights) / 2)):
                self.model.net[2 * i].weight = torch.nn.Parameter(self.weights[2 * i])
                self.model.net[2 * i].bias = torch.nn.Parameter(self.weights[(2 * i) + 1])
            outputs = self.model.net(torch.tensor(inputs, dtype=torch.float))

            if (0 < self.pos[0] < self.model.grid.width - 1) and (0 < self.pos[1] < self.model.grid.height - 1):
                immediate_neighborhood = self.model.grid.get_neighborhood(self.pos, moore=False,
                                                                          include_center=True)
            else:
                immediate_neighborhood = self.generate_neighborhood_pad()

            move = torch.argmax(outputs)
            immediate_neighborhood.append(self.random.choice(immediate_neighborhood))
            if self.model.grid.is_cell_empty(immediate_neighborhood[move]):
                self.model.grid.move_agent(self, immediate_neighborhood[move])
            else:
                self.model.grid.move_agent(self, self.pos)

    def die(self):
        self.model.grid.move_to_empty(self)

    def generate_neighborhood_pad(self):
        if self.pos[0] == 0 and self.pos[1] == 0:
            immediate_neighborhood = [self.pos, self.pos, self.pos, (self.pos[0], self.pos[1] + 1),
                                      (self.pos[0] + 1, self.pos[1])]
        elif self.pos[0] == 0 and self.pos[1] == self.model.grid.height - 1:
            immediate_neighborhood = [self.pos, (self.pos[0], self.pos[1] - 1), self.pos, self.pos,
                                      (self.pos[0] + 1, self.pos[1])]
        elif self.pos[0] == 0:
            immediate_neighborhood = [self.pos, (self.pos[0], self.pos[1] - 1), self.pos,
                                      (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1])]
        elif self.pos[0] == self.model.grid.width - 1 and self.pos[1] == 0:
            immediate_neighborhood = [(self.pos[0] - 1, self.pos[1]), self.pos, self.pos,
                                      (self.pos[0], self.pos[1] + 1), self.pos]
        elif self.pos[0] == self.model.grid.width - 1 and self.pos[1] == self.model.grid.height - 1:
            immediate_neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      self.pos, self.pos]
        elif self.pos[0] == self.model.grid.width - 1:
            immediate_neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      (self.pos[0], self.pos[1] + 1), self.pos]
        elif self.pos[1] == 0:
            immediate_neighborhood = [(self.pos[0] - 1, self.pos[1]), self.pos, self.pos,
                                      (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1])]
        elif self.pos[1] == self.model.grid.height - 1:
            immediate_neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      self.pos, (self.pos[0] + 1, self.pos[1])]
        else:
            immediate_neighborhood = [(self.pos[0] - 1, self.pos[1]), (self.pos[0], self.pos[1] - 1),
                                      self.pos,
                                      (self.pos[0], self.pos[1] + 1), (self.pos[0] + 1, self.pos[1])]

        return immediate_neighborhood

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
        immediate_neighborhood = self.generate_neighborhood_pad()
        immediate_neighborhood.pop(2)
        for idx, x in enumerate(immediate_neighborhood):
            if x == self.pos:
                immediate_neighborhood[idx] = 1
            elif self.model.grid.is_cell_empty(x):
                immediate_neighborhood[idx] = 2/3
            else:
                immediate_neighborhood[idx] = 1/3
        return [self.model.age / self.model.max_age, 0.7 if (self.colour == 1) else 0.3] + [
            self.pos[0] / (self.model.grid.width - 1), self.pos[1] / (self.model.grid.height - 1)] + immediate_neighborhood


class GridColour(Agent):
    def __init__(self, unique_id, model, colour):
        super().__init__(unique_id, model)
        self.colour = colour
        self.type = "GridColour"

    def step(self):
        # The agent's step will go here
        self.model.grid.move_agent(self, self.pos)
