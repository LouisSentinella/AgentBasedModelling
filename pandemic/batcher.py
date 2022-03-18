import pandas as pd

from models import *
import matplotlib.pyplot as plt
from tqdm import tqdm

if __name__ == "__main__":
    for percent in [0.1, 0.2, 0.225, 0.25, 0.275, 0.3, 0.4, 0.5, 0.75, 1.0]:
        # TODO: get in depth recordings for each percent
        # TODO: compare to recordings with different asymptomatic rate and different lockdown rules
        model = PandemicModel(n=400, width=50, height=50, masked_percentage=percent, asymptomatic_probability=0.2,
                              infection_length=10, infection_probability=0.12, time_till_symptoms=5, quarantine_length=14,
                              immunity_length=50, n_workplaces=25, n_shops=5, n_schools=2, n_churches=2, n_couples=150,
                              couples_with_kids_percentage=0.7, initial_infected_percentage=0.005, house_depth=4,
                              lockdown_threshold=0.05, liftlockdown_threshold=0.01)
        num_epochs = 250
        num_gens = 24 * 365
        start_gen = 0
        dead_series = pd.Series([0 for _ in range(num_gens)], dtype=int)
        infected_series = pd.Series([0 for _ in range(num_gens)], dtype=int)
        for i in tqdm(range(num_epochs)):
            for j in range(start_gen, num_gens):
                model.step()
            infected_amount = model.datacollector.get_model_vars_dataframe()["Infected"]
            infected_series = infected_series.add(infected_amount)
            dead_amount = model.datacollector.get_model_vars_dataframe()["Dead"]
            dead_series = dead_series.add(dead_amount)
            model = PandemicModel(n=400, width=50, height=50, masked_percentage=percent, asymptomatic_probability=0.2,
                                  infection_length=10, infection_probability=0.12, time_till_symptoms=5,
                                  quarantine_length=14, immunity_length=50, n_workplaces=25, n_shops=5, n_schools=2,
                                  n_churches=2, n_couples=150, couples_with_kids_percentage=0.7,
                                  initial_infected_percentage=0.005, house_depth=4, lockdown_threshold=0.05,
                                  liftlockdown_threshold=0.01)
        divisor_series = pd.Series([num_epochs for _ in range(num_gens)], dtype=float)
        infected_series = infected_series / divisor_series
        dead_series = dead_series / divisor_series
        plt.plot(infected_series, label=f"Infected at {model.masked_percentage}")
        plt.legend(loc="upper right")
        plt.savefig(f"images/infected_at_{model.masked_percentage}.png")
        plt.show()
        plt.plot(dead_series, label=f"Dead at {model.masked_percentage}")
        plt.legend(loc="upper right")
        plt.savefig(f"images/dead_at_{model.masked_percentage}.png")
        plt.show()
