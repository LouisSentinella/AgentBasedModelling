import numpy as np
import pandas as pd

from models import *
import matplotlib.pyplot as plt
from tqdm import tqdm

if __name__ == "__main__":
    independent_variable = [x/10 for x in range(0, 11)]
    comparison_df = pd.DataFrame([[x, 0, 0] for x in independent_variable], columns=["Percent","Dead", "Total_Cases"])
    for percent in independent_variable:
        # TODO: get in depth recordings for each percent
        # TODO: compare to recordings with different asymptomatic rate and different lockdown rules
        model = PandemicModel(n=400, width=50, height=50, masked_percentage=percent, asymptomatic_probability=0.2,
                              infection_length=15, infection_probability=0.12, time_till_symptoms=5,
                              quarantine_length=14,
                              immunity_length=50, n_workplaces=25, n_shops=5, n_schools=2, n_churches=2, n_couples=150,
                              couples_with_kids_percentage=0.7, initial_infected_percentage=0.005, house_depth=4,
                              lockdown_threshold=0.05, liftlockdown_threshold=0.01)
        num_epochs = 10
        num_gens = 24 * 365
        start_gen = 0
        total_df = pd.DataFrame(np.zeros((num_gens, 3)), columns=["Infected", "Dead", "Total_Cases"])
        for i in tqdm(range(num_epochs)):
            for j in range(start_gen, num_gens):
                model.step()
            model_dataframe = model.datacollector.get_model_vars_dataframe()
            for x in ["Dead", "Infected", "Total_Cases"]:
                total_df[x] = total_df[x].add(model_dataframe[x])

            model = PandemicModel(n=400, width=50, height=50, masked_percentage=percent, asymptomatic_probability=0.2,
                                  infection_length=10, infection_probability=0.12, time_till_symptoms=5,
                                  quarantine_length=14, immunity_length=50, n_workplaces=25, n_shops=5, n_schools=2,
                                  n_churches=2, n_couples=150, couples_with_kids_percentage=0.7,
                                  initial_infected_percentage=0.005, house_depth=4, lockdown_threshold=0.05,
                                  liftlockdown_threshold=0.01)
        divisor_series = pd.Series([num_epochs for _ in range(num_gens)], dtype=float)
        for x in ["Dead", "Infected", "Total_Cases"]:
            total_df[x] = total_df[x] / divisor_series
            plt.plot(total_df[x], label=f"{x}")
            plt.legend(loc="upper right")
            plt.savefig(f"images/masks_and_quar/{x}_at_{percent}_masks_and_regular_quar.png")
            plt.show()
        comparison_df[comparison_df["Percent"] == percent] = [percent, total_df["Dead"].iloc[-1], total_df["Total_Cases"].iloc[-1], ]
