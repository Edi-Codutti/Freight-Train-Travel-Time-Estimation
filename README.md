# Freight-Train-Travel-Time-Estimation
This project aims to provide an implementation of [this problem](https://www.sciencedirect.com/science/article/pii/S0377221721007207) using python and Gurobi.

## File description
- `solver.py` consists only of a class that contains the gurobi solver loaded with all the variables, contraints and the objective function
- `test.py` contains a toy problem to test the solver (data can be found [here](https://higherlogicdownload.s3.amazonaws.com/INFORMS/e52cec4c-eedb-4c3b-a379-8408d89f8fc9/UploadedImages/Problem_Solving/2020_Competition/RAS-PSC_ToyProb_20200522.xlsx))
- `problem.py` contains the real problem. It is divided into 2 separate days that can be selected indipendently as a command line argument
- `scalability.py` contains the code to help users in the scalability analysis considering both time and memory usage
- `plots.py` is a script to plot the most important results given by the solver (`train_mvmt_estimation.csv`, `deviations.csv`). **Note:** this file was created to compare our results with the ones in the original paper, so train movement data works only on day 1
- `RAS-PSC_ValDataset_20200609-06.xlsx` is a cleaned version of the dataset that can be found [here](https://connect.informs.org/railway-applications/new-item3/problem-solving-competition682/problem-solving-competition681311): the original one contains errors
- `train_mvmt_estimation.csv` is a file created by `problem.py` that contains the estimated train movement data for the selected day (departure and arrival at each station for each train)
- `deviations.csv` is a file created by `problem.py` that contains the deviation in hours from the original schedule of every train at the destination station for one day
- `ram_usage_auto.csv`, `ram_usage_simplex.csv` are files containing information abount the memory usage of the solver in the case of automatic selection of the algorithm for the continuous relaxation and the case when this algorithm is selected as *deterministic concurrent simplex*

## Libraries used in the project
- gurobipy
- numpy
- pandas
- matplotlib
- seaborn