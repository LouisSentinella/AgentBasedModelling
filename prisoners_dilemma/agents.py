from mesa import Agent
import random


class GameAgent(Agent):
    """ An agent that is more likely to choose the mean option. """

    def __init__(self, unique_id, model, home_cell=None):
        super().__init__(unique_id, model)
        self.score = 1
        self.home_cell = home_cell
        self.spouse = None
        self.partner = None
        self.choice = None
        self.age = 0
        self.children = []
        self.dead_spouse = False
        self.health = 10

    def __str__(self):
        return f"Agent {self.unique_id}, with score {self.score}. \n Home cell: {str(self.home_cell)}, Spouse: {self.spouse.unique_id if self.spouse else None}. \n Age: {self.age}, Children: {str([[child.age, child.home_cell == self.home_cell] for child in self.children])}. \n Had spouse: {str(self.dead_spouse)}"

    def step(self):
        if self.health < 1 or self.age > 85:
            adult_at_home = [child for child in self.children if
                             ((child.age >= 18) and (child.home_cell == self.home_cell))]
            children_at_home = [child for child in self.children if child.age < 18]
            parents_at_home = [parent for parent in self.parents if parent.home_cell == self.home_cell]
            for child in self.children:
                child.parents.remove(self)
            for parent in self.parents:
                parent.children.remove(self)
            if self.spouse:
                self.spouse.dead_spouse = True
                self.spouse.spouse = None
            else:
                if len(adult_at_home) == 0:

                    if len(children_at_home) > 0:
                        for child in children_at_home:
                            self.model.schedule.remove(child)
                            self.model.grid.remove_agent(child)
                        self.children = []
                    if len(parents_at_home) == 0:
                        if self.home_cell not in self.model.unoccupied_houses:
                            self.model.unoccupied_houses.append(self.home_cell)
                        if self.home_cell in self.model.occupied_houses:
                            self.model.occupied_houses.remove(self.home_cell)
                else:
                    for child in children_at_home:
                        new_parent = random.choice(adult_at_home)
                        new_parent.children.append(child)
                        child.parents.append(new_parent)

            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)

        else:
            if self.age < 18:
                if self.model.time != "night":
                    pass
                else:
                    self.age += 1
            elif self.spouse is None and len([child for child in self.children if child.spouse is None]) == 0:
                if self.model.time == "morning":
                    self.move(mingle=True)
                elif self.model.time == "midday":
                    if self.partner:
                        self.move_in()
                elif self.model.time == "afternoon":
                    self.move(destination=self.home_cell)
                elif self.model.time == "evening":
                    if self.spouse:
                        self.reproduce()
                else:
                    self.sleep()
            else:
                if self.model.time == "morning":
                    self.move()
                elif self.model.time == "midday":
                    if self.partner:
                        self.choose_action()
                elif self.model.time == "afternoon":
                    self.move(destination=self.home_cell)
                elif self.model.time == "evening":
                    if self.spouse:
                        self.reproduce()
                else:
                    self.sleep()

    def move(self, destination=None, mingle=False):
        if destination is None:
            # Find other player to play with and move to their cell
            # If no other player, move randomly
            if mingle:
                other_players = self.model.out_minglers
            else:
                other_players = self.model.out_agents
            if len(other_players) > 0:
                other_player = random.choice(other_players)
                self.partner = other_player
                other_player.partner = self
                self.move(other_player.pos)
                other_players.remove(other_player)
            else:
                # Move to random cell
                random_cell = (
                    random.randint(1, self.model.grid.width - 2), random.randint(1, self.model.grid.height - 2))
                while not self.model.grid.is_cell_empty(random_cell):
                    random_cell = (
                        random.randint(1, self.model.grid.width - 2), random.randint(1, self.model.grid.height - 2))
                self.move(destination=random_cell)
                other_players.append(self)
        else:
            # Move to destination cell
            self.model.grid.move_agent(self, destination)
            self.pos = destination

    def reproduce(self):
        type_dict = {"mean": MeanAgent, "altruistic": AltruisticAgent, "greenbeard": GreanBeardAltruistic,
                     "imposter": ImposterGreenBeards, "spiteful_family": SpitefulFamily, "spiteful": Spiteful, "tft": TitForTat,
                     "tft_family": TitForTatFamily}
        # print("Trying for babys")
        if self.score > 10 and self.spouse.score > 10:
            # Create new agent
            if 18 < self.age < 55 and 18 < self.spouse.age < 55:
                # print("BABY!")
                num_children = random.randint(1, 2)
                for i in range(num_children):
                    child_type = random.choice([self.type, self.spouse.type])
                    self.model.num_agents += 1
                    child = type_dict[child_type](self.model.num_agents, self.model)
                    child.home_cell = self.home_cell
                    self.model.schedule.add(child)
                    self.model.grid.place_agent(child, child.home_cell)
                    self.children.append(child)
                    self.spouse.children.append(child)
                    child.parents = [self, self.spouse]
                self.score -= 10
                self.spouse.score -= 10

    def sleep(self):
        food_to_eat = self.model.harshness * (1 + sum(
            0.5 for child in self.children if child.home_cell == self.home_cell and child.age >= 18) + sum(
            0.3 for child in self.children if child.home_cell == self.home_cell and child.age < 18))
        if self.score < food_to_eat:
            self.health -= 20
            for child in self.children:
                if child.home_cell == self.home_cell:
                    child.health -= 20
        else:
            self.score -= food_to_eat
            self.health += 10
            for child in self.children:
                if child.home_cell == self.home_cell:
                    child.health += 10
        self.age += 1

    def move_in(self):
        if self.age - 5 <= self.partner.age <= self.age + 5:
            if len(self.model.unoccupied_houses) > 0:
                # Move to random unoccupied house
                self.home_cell = random.choice(self.model.unoccupied_houses)
                self.partner.home_cell = self.home_cell
                self.spouse = self.partner
                self.partner.spouse = self
                self.model.unoccupied_houses.remove(self.home_cell)
                self.model.occupied_houses.append(self.home_cell)

    def fight(self):
        # Prisoner's dilemma
        if self.choice == "cooperate":
            if self.partner.choice == "cooperate":
                self.score += 3
                self.partner.score += 3
            else:
                self.score += 0
                self.partner.score += 5
        else:
            if self.partner.choice == "cooperate":
                self.score += 5
                self.partner.score += 0
            else:
                self.score += 1
                self.partner.score += 1
        self.choice = None
        self.partner.choice = None


class MeanAgent(GameAgent):
    """ An agent that is more likely to choose the mean option. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "mean"

    def choose_action(self):
        # Choose action
        self.choice == "defect"
        if self.partner.choice:
            self.fight()


class AltruisticAgent(GameAgent):
    """ An agent that is more likely to be altruistic. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "altruistic"

    def choose_action(self):
        # Choose action
        self.choice = "cooperate"
        if self.partner.choice:
            self.fight()


class GreanBeardAltruistic(GameAgent):
    """ An agent that is more likely to be altruistic to other greenbeards."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "greenbeard"

    def choose_action(self):
        # Choose action

        if self.partner.type == "greenbeard" or self.partner.type == "imposter":
            self.choice = "cooperate"
        else:
            self.choice = "defect"

        if self.partner.choice:
            self.fight()


class ImposterGreenBeards(GameAgent):
    """ An agent who pretends to be a green beard to take advantage of the other greenbeard's altruism."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "imposter"

    def choose_action(self):
        # Choose action
        if self.partner.type == "greenbeard" or self.partner.type == "imposter":
            self.choice = "defect"
        else:
            self.choice = "cooperate"

        if self.partner.choice:
            self.fight()


class SpitefulFamily(GameAgent):
    """ An agent who pretends is altruistic, unless they have been betrayed before. At which point they (and their
    family) will defect. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "spiteful_family"
        self.wronged_list = []

    def choose_action(self):
        # Choose action
        if self.partner in self.wronged_list:
            self.choice = "defect"
        else:
            self.choice = "cooperate"

        if self.partner.choice:
            self.fight()

    def tell_related(self, agent):
        # Tells the other agent that they have been wronged
        list_of_family = self.children + [self.partner] + self.parents + [[i for i in child.children] for child in
                                                                          self.children]
        for member in list_of_family:
            if member.type == "spiteful_family":
                member.wronged_list.append(agent)

    def fight(self):
        super().fight()
        if self.partner.choice == "defect":
            if self.partner not in self.wronged_list:
                self.wronged_list.append(self.partner)
                self.tell_related(self.partner)


class Spiteful(GameAgent):
    """ An agent who pretends is altruistic, unless they have been betrayed before. At which point they will defect. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "spiteful"
        self.wronged_list = []

    def choose_action(self):
        # Choose action
        if self.partner in self.wronged_list:
            self.choice = "defect"
        else:
            self.choice = "cooperate"

        if self.partner.choice:
            self.fight()

    def fight(self):
        super().fight()
        if self.partner.choice == "defect":
            if self.partner not in self.wronged_list:
                self.wronged_list.append(self.partner)


class TitForTat(GameAgent):
    """ Classical Tit for Tat strategy. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "tft"
        self.wronged_list = []

    def choose_action(self):
        # Choose action
        if self.partner in self.wronged_list:
            self.choice = "defect"
        else:
            self.choice = "cooperate"

        if self.partner.choice:
            self.fight()

    def fight(self):
        super().fight()
        if self.partner.choice == "defect":
            if self.partner not in self.wronged_list:
                self.wronged_list.append(self.partner)
        else:
            if self.partner in self.wronged_list:
                self.wronged_list.remove(self.partner)


class TitForTatFamily(GameAgent):
    """ Classical Tit for Tat strategy. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "tft_family"
        self.wronged_list = []

    def choose_action(self):
        # Choose action
        if self.partner in self.wronged_list:
            self.choice = "defect"
        else:
            self.choice = "cooperate"

        if self.partner.choice:
            self.fight()

    def fight(self):
        super().fight()
        if self.partner.choice == "defect":
            if self.partner not in self.wronged_list:
                self.wronged_list.append(self.partner)
                self.tell_related(self.partner)
        else:
            if self.partner in self.wronged_list:
                self.wronged_list.remove(self.partner, remove=True)

    def tell_related(self, agent, remove=False):
        # Tells the other agent that they have been wronged
        list_of_family = self.children + [self.partner] + self.parents + [[i for i in child.children] for child in
                                                                          self.children]
        for member in list_of_family:
            if member.type == "tft_family":
                if remove:
                    member.wronged_list.remove(agent)
                else:
                    member.wronged_list.append(agent)