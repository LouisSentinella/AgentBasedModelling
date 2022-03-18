import random

from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import SimultaneousActivation, RandomActivation
from mesa import Model
from agents import *


class PandemicModel(Model):

    def __init__(self, n, couples_with_kids_percentage, n_couples, width, height, masked_percentage, infection_length,
                 infection_probability, time_till_symptoms, quarantine_length, immunity_length, n_workplaces, n_shops,
                 n_schools, n_churches, initial_infected_percentage, house_depth, asymptomatic_probability, lockdown_threshold, liftlockdown_threshold):

        self.lockdown_active = False
        self.n = n
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector(
            model_reporters={"Dead": self.get_dead_amount, "Infected": self.get_infected_amount, "Uninfected": self.get_uninfected_amount, "Alive": self.get_alive_amount},
        )
        self.asymptomatic_probability = asymptomatic_probability
        self.masked_percentage = masked_percentage
        self.infection_length = infection_length
        self.infection_probability = infection_probability
        self.time_till_symptoms = time_till_symptoms
        self.quarantine_length = quarantine_length
        self.immunity_length = immunity_length
        self.age = 0
        self.time = 0
        self.lockdown_threshold = lockdown_threshold
        self.liftlockdown_threshold = liftlockdown_threshold
        self.empty_house_cells = self.generate_empty_house_cells(house_depth)
        if (n - (n_couples * 2)) + n_couples > len(self.empty_house_cells):
            raise ValueError("Too many people in the model")
        self.unused_cells = [x for x in self.grid.empties if x not in self.empty_house_cells]
        self.schools, self.workplaces, self.shops, self.churches = self.generate_features(n_schools, n_workplaces, n_shops, n_churches)
        self.create_agents(couples_with_kids_percentage, n_couples, n - n_couples * 2)
        self.infect_agents(initial_infected_percentage)
        self.dead_people = 0
        self.running = True

    def step(self):
        self.schedule.step()
        self.time = (self.time + 1) % 24
        if self.time == 0:
            self.age += 1
        if self.get_infected_amount() / len(self.schedule.agents) > self.lockdown_threshold:
            self.lockdown()
            self.lockdown_active = True
        if self.get_infected_amount() / len(self.schedule.agents) < self.liftlockdown_threshold and self.lockdown_active:
            self.lift_lockdown()
            self.lockdown_active = False
        self.datacollector.collect(self)

    def create_agents(self, children_percentage, n_couples, n_single):
        type_dict = {"Masked": MaskedPerson, "Unmasked": UnmaskedPerson}

        for i in range(n_single):
            house = self.assign_house_cell()
            if i < n_single * self.masked_percentage:
                new_agent = MaskedPerson(len(self.schedule.agents), self, house, self.random.randint(18, 65))
            else:
                new_agent = UnmaskedPerson(len(self.schedule.agents), self, house, self.random.randint(18, 65))
            self.schedule.add(new_agent)
            self.grid.place_agent(new_agent, self.assign_house_cell())

        for i in range(n_couples):
            couple_house = self.assign_house_cell()
            ages = [self.random.randint(18, 65)]
            ages.append(self.random.randint(ages[0] - 5, ages[0] + 5))
            for j in range(2):
                if i < n_couples * self.masked_percentage:
                    new_agent = MaskedPerson(len(self.schedule.agents), self, couple_house, ages.pop())
                else:
                    new_agent = UnmaskedPerson(len(self.schedule.agents), self, couple_house, ages.pop())

                self.schedule.add(new_agent)
                self.grid.place_agent(new_agent, couple_house)
            self.schedule.agents[-1].set_spouse(self.schedule.agents[-2])
            if i < n_couples * children_percentage:
                new_agent = type_dict[self.schedule.agents[-1].type](len(self.schedule.agents), self, couple_house, self.random.randint(0, 17))
                self.schedule.add(new_agent)
                self.grid.place_agent(new_agent, couple_house)


    def generate_empty_house_cells(self, depth=1):
        empty_house_cells = []
        for i in range(1, depth+1):
            for x in [i-1, self.grid.width - i]:
                for y in range(self.grid.height - i):
                    empty_house_cells.append((x, y))
            for y in [i-1, self.grid.height - i]:
                for x in range(i, self.grid.width - (i + 1)):
                    empty_house_cells.append((x, y))

        return empty_house_cells

    def assign_house_cell(self):
        return self.empty_house_cells.pop(self.random.randint(0, len(self.empty_house_cells) - 1))

    def generate_features(self, n_schools, n_workplaces, n_shops, n_churches):
        schools = [self.unused_cells.pop(self.random.randint(0, len(self.unused_cells) - 1)) for _ in range(n_schools)]
        workplaces = [self.unused_cells.pop(self.random.randint(0, len(self.unused_cells) - 1)) for _ in range(n_workplaces)]
        shops = [self.unused_cells.pop(self.random.randint(0, len(self.unused_cells) - 1)) for _ in range(n_shops)]
        churches = [self.unused_cells.pop(self.random.randint(0, len(self.unused_cells) - 1)) for _ in range(n_churches)]
        return schools, workplaces, shops, churches

    def infect_agents(self, initial_infected_percentage):
        for agent in self.schedule.agents:
            if self.random.random() < initial_infected_percentage:
                agent.infect()
        self.random.choice(self.schedule.agents).infect()

    def lockdown(self):
        for agent in self.schedule.agents:
            agent.active_schedule = agent.lockdown_schedule if not agent.quarantined else agent.quarantine_schedule
            if agent.type == "Masked":
                agent.mask_wear_rate = 1


    def lift_lockdown(self):
        for agent in self.schedule.agents:
            agent.active_schedule = agent.normal_schedule if not agent.quarantined else agent.quarantine_schedule

    def get_dead_amount(self):
        return self.dead_people

    def get_infected_amount(self):
        return len([agent for agent in self.schedule.agents if agent.infected])

    def get_uninfected_amount(self):
        return len(self.schedule.agents) - self.get_infected_amount()

    def get_alive_amount(self):
        return len(self.schedule.agents)
