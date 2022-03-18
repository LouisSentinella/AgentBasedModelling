from mesa import Agent


class Person(Agent):
    """
    A person in the model.
    """

    def __init__(self, unique_id, model, house, age):
        super().__init__(unique_id, model)
        self.asymptomatic = None
        self.house = house
        self.age = age
        self.infected = False
        self.quarantined = False
        self.time_infected = 0
        self.time_quarantined = 0
        self.immune = False
        self.time_recovered = 0
        self.spouse = None
        self.default_type = "Person"
        self.type = self.default_type
        self.infection_modifier = 1

        if self.age > 60:
            self.death_probability = 0.1
        elif self.age > 40:
            self.death_probability = 0.03
        elif self.age > 20:
            self.death_probability = 0.01
        else:
            self.death_probability = 0.005

        self.normal_schedule, self.lockdown_schedule = self.generate_daily_schedule()
        self.quarantine_schedule = [[self.house for _ in range(24)] for _ in range(7)]
        self.active_schedule = self.normal_schedule

    def step(self):
        """
        Agent's step
        :return:
        """
        if self.infected:
            self.time_infected += 1
            if self.time_infected == self.model.infection_length * 24:
                self.infected = False
                self.immune = True
                self.time_recovered = 0
                self.time_infected = 0
            if not self.quarantined and self.time_infected >= self.model.time_till_symptoms * 24 and not self.asymptomatic and self.random.random() < 0.5:
                self.quarantine_toggle()


            if len(self.model.grid.grid[self.pos[0]][self.pos[1]]) > 1:
                for agent in self.model.grid.grid[self.pos[0]][self.pos[1]]:
                    if not agent.infected and not agent.immune:
                        self.interact(agent)
        if self.immune:
            self.time_recovered += 1
            if self.time_recovered == self.model.immunity_length * 24:
                self.immune = False
                self.time_recovered = 0

        if self.quarantined:
            self.time_quarantined += 1
            if self.time_quarantined == self.model.quarantine_length * 24:
                self.quarantine_toggle()

        self.model.grid.move_agent(self, self.active_schedule[self.model.age % 7][self.model.time])
        if self.infected:
            if self.time_infected == self.death_attempt_day * 24:
                if self.random.random() < self.death_probability:
                    self.die()

    def interact(self, other):
        if self.infected and not other.infected and not other.immune and not self.active_schedule[self.model.age % 7][
                                                                                 self.model.time - 1] == \
                                                                             other.active_schedule[other.age % 7][
                                                                                 other.model.time - 1]:
            self.attempt_infection(other)

    def attempt_infection(self, other):
        if self.model.random.random() < (
                self.model.infection_probability * (self.infection_modifier * other.infection_modifier)):
            other.infect()

    def infect(self):
        self.infected = True
        self.time_infected = 0
        self.model.total_cases += 1
        self.type = "Infected"
        self.asymptomatic = self.model.random.random() < self.model.asymptomatic_probability
        self.death_attempt_day = self.model.random.randint(0, self.model.infection_length - 1)

    def set_spouse(self, spouse):
        self.spouse = spouse
        spouse.spouse = self

    def quarantine_toggle(self):
        self.quarantined = not self.quarantined
        self.type = "Quarantined" if self.quarantined else self.default_type
        self.active_schedule = self.quarantine_schedule if self.quarantined else (self.normal_schedule if not self.model.lockdown_active else self.lockdown_schedule)


    def generate_daily_schedule(self):
        schedule = [[self.house for _ in range(24)] for _ in range(7)]
        lockdown_schedule = [[self.house for _ in range(24)] for _ in range(7)]
        if self.age > 17:
            work_place = self.random.choice(self.model.workplaces)
        else:
            work_place = self.random.choice(self.model.schools)
        shop = self.random.choice(self.model.shops)
        for j in range(0, 4):
            for i in range(9, 17):
                schedule[j][i] = work_place
                if self.age > 17:
                    if self.random.random() < 0.2:
                        lockdown_schedule[j][i] = work_place
            if self.random.random() < 0.4:
                for i in range(18, 20):
                    schedule[j][i] = shop
                if self.random.random() < 0.05:
                    for i in range(18, 20):
                        lockdown_schedule[j][i] = shop

        if self.random.random() < 0.8:
            shop_time = self.random.randint(10, 20)
            for i in range(shop_time, shop_time + 2):
                schedule[5][i] = shop

            if self.random.random() < 0.05:
                for i in range(shop_time, shop_time + 2):
                    lockdown_schedule[5][i] = shop

        if self.spouse:
            schedule[6][10] = self.spouse.daily_schedule[6][10]
            lockdown_schedule[6][10] = self.spouse.lockdown_schedule[6][10]
        else:
            if self.random.random() < 0.5:
                church_choice = self.random.choice(self.model.churches)
                schedule[6][10] = church_choice
                if self.random.random() < 0.05:
                    lockdown_schedule[6][10] = church_choice

        return schedule, lockdown_schedule

    def die(self):
        if self.spouse:
            self.spouse.spouse = None
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)
        self.model.dead_people += 1



class MaskedPerson(Person):

    def __init__(self, unique_id, model, house, age):
        super().__init__(unique_id, model, house, age)
        self.default_type = "Masked"
        self.type = self.default_type
        self.mask_wear_rate = 0.4
        self.infection_modifier = 0.5 * self.mask_wear_rate


class UnmaskedPerson(Person):

    def __init__(self, unique_id, model, house, age):
        super().__init__(unique_id, model, house, age)
        self.default_type = "Unmasked"
        self.type = self.default_type
