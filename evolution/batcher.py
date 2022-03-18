from models import *
import matplotlib.pyplot as plt
from tqdm import tqdm
import tracemalloc
load = True
if __name__ == "__main__":
    model = FourRaceClassificationModel(n=100, width=35, height=35, mutation_rate=0.1, max_age=200)
    model.save_iterator = 100
    graph_iterator = 50
    num_gens = 10_000
    start_gen = 0
    if load:
        model = pickle.load(open("saved_models/four_race_deep/race_evolution_700.pkl", "rb"))
        start_gen = 700
        #model.mutation_rate = 0.001
    for j in tqdm(range(start_gen, num_gens)):
        for i in range(model.max_age):
            model.step()
        if j % graph_iterator == 0:
            plt.plot(model.datacollector.get_model_vars_dataframe()["Correct"])
            plt.show()
    # for stat in model.snap.statistics('lineno')[:20]:
    #     print(stat)
    plt.plot(model.datacollector.get_model_vars_dataframe()["Correct"])
    plt.show()
