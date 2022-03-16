from models import *
import matplotlib.pyplot as plt
from tqdm import tqdm
import tracemalloc

if __name__ == "__main__":
    model = RaceClassificationModel(n=200, width=50, height=50, mutation_rate=0.005, max_age=100, save_path="saved_models/big_long/race_evolution_")
    model.save_iterator = 50
    graph_iterator = 50
    for j in tqdm(range(1000)):
        for i in range(model.max_age):
            model.step()
        if j % graph_iterator == 0:
            plt.plot(model.datacollector.get_model_vars_dataframe()["Correct"])
            plt.show()

    plt.plot(model.datacollector.get_model_vars_dataframe()["Correct"])
    plt.show()
