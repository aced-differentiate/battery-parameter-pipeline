from sqlalchemy import create_engine
import numpy as np
import json
import pickle
import pandas as pd


class DFNDatabase:
    def __init__(self):
        db_connection = {
            "address": "dfn-parameters.postgres.database.azure.com",
            "port": "5432",
            "username": "liiondb@dfn-parameters",
            "password": "Multi-Scale Modelling Project",
            "dbname": "dfndb",
        }
        postgres_str = (
            "postgresql://{username}:{password}@{ipaddress}:{port}/{dbname}".format(
                username=db_connection["username"],
                password=db_connection["password"],
                ipaddress=db_connection["address"],
                port=db_connection["port"],
                dbname=db_connection["dbname"],
            )
        )
        self.db = create_engine(postgres_str)

    def read_sql(self, query):
        return pd.read_sql(query, self.db)

    def get_id_list(self, query):
        df = self.read_sql(query)
        id_list = df["data_id"].to_list()
        return id_list

    def extract_data(self, query, T):
        """
        Parameters
        ----------
        T : float
            Temperature in Kelvin
        """
        # Looping through and plotting
        id_list = self.get_id_list(query)
        id_to_data = {}
        for data_id in id_list:
            query = f"SELECT * FROM data WHERE data_id = {data_id};"
            df = dfndb.read_sql(query)
            metatada = {
                "paper": df.paper_id[0],
                "material": df.material_id[0],
                "parameter": df.parameter_id[0],
            }

            # Reading the raw data either in value, array, or function format
            data = read_data(df)

            if df.raw_data_class[0] == "array":
                x = data[:, 0]
                y = data[:, 1]

            else:
                x_range = df.input_range.to_numpy()[0]
                x_min = float(x_range.lower) + 0.001
                x_max = float(x_range.upper) - 0.001
                if df.raw_data_class[0] == "function":
                    x_min += 0.001
                    x_max -= 0.001
                    x = np.linspace(x_min, x_max)
                    try:
                        y = data(x, T)
                    except:
                        y = data(x)

                elif df.raw_data_class[0] == "value":
                    n = 10
                    x = np.linspace(x_min, x_max)
                    y = data * np.ones(n)

            print(metatada)
            id_to_data[data_id] = {"x": x, "y": y, "metadata_id": metatada}

        return id_to_data


def read_data(df):
    raw_data_class = df["raw_data_class"][0]

    if raw_data_class == "value":
        return float(df["raw_data"][0])
    elif raw_data_class == "function":
        function_binary = df["function"][0]
        # creates "function"
        # unpickle
        # function = pickle.loads(function_binary)
        function = lambda x: x * np.nan
        return function
    elif raw_data_class == "array":
        csv_array = df["raw_data"][0]
        csv_array = csv_array.replace("{", "[").replace("}", "]")
        return np.array(json.loads(csv_array))


def plot_loop(dfndb, id_to_data):
    # plot data id list in a loop fashion
    import matplotlib.pyplot as plt

    # Plot display settings
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100)

    # Label font sizes
    SMALL_SIZE = 8
    MEDIUM_SIZE = 10
    BIGGER_SIZE = 15

    # Looping through and plotting
    for data in id_to_data.values():
        x = data["x"]
        y = data["y"]
        print(x, y)
        metadata = data["metadata_id"]

        # query and assign the legend and axes label strings
        paper_id = metadata["paper"]
        query = f"SELECT paper.paper_tag FROM paper WHERE paper_id = {paper_id};"
        paper_string = dfndb.read_sql(query).paper_tag[0]

        material_id = metadata["material"]
        query = f"SELECT material.name FROM material WHERE material_id = {material_id};"
        material_string = dfndb.read_sql(query).name[0]

        leg_string = f"{material_string}, {paper_string}"
        ax.plot(x, y, "-", label=leg_string)

        parameter_id = metadata["parameter"]
        query = f"SELECT * FROM parameter WHERE parameter_id = {parameter_id};"
        paramdf = dfndb.read_sql(query)

        xlabel = f"[{paramdf.units_input[0]}]"
        ax.set_xlabel(xlabel)

        y_param = paramdf.name[0]
        y_unit = paramdf.units_output[0]
        ylabel = f"{y_param} [{y_unit}]"
        ax.set_ylabel(ylabel)

    fig.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

    # plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    # plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    # plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    # plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    # plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    # plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
    # plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title
    # plt.rcParams["axes.linewidth"] = 1

    plt.show()


if __name__ == "__main__":
    dfndb = DFNDatabase()
    query = """
            SELECT DISTINCT data.data_id,parameter.symbol,parameter.name as parameter, material.name as material,data.raw_data, parameter.units_input, parameter.units_output, paper.paper_tag, paper.doi
            FROM data
            JOIN paper ON paper.paper_id = data.paper_id
            JOIN material ON material.material_id = data.material_id
            JOIN parameter ON parameter.parameter_id = data.parameter_id
            WHERE parameter.name = 'half cell ocv'
            AND material.lfp = 1
            LIMIT 5
            """
    id_list = dfndb.get_id_list(query)
    id_to_data = dfndb.extract_data(query, T=298)
    plot_loop(dfndb, id_to_data)
