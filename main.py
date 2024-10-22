import pandas as pd
from RangedEntitiesFinder import RangedEntitiesFinder as rEF
from EntitiesGenerator import EntitiesGenerator
import openpyxl

if __name__ == "__main__":
    # Reading data from Excel into DataFrames.
    #total_df = pd.read_excel(r"data/dataTables.xlsx", "total", converters={"id": str})
    #sus_df = pd.read_excel(r"data/dataTables.xlsx", "sus", converters={"id": str})

    num_entities = 5
    num_tracks = 10

    (total_df, sus_df) = EntitiesGenerator.generate_entities_paths(num_entities, num_tracks, False)

    print("--- Enter max distance from target in km (or enter 's' to quit, or 'r' to generate new data) ---")

    max_distance_from_target = None

    while max_distance_from_target != 's':
        max_distance_from_target = input("\nYour input (a number, 's', or 'r'): ")

        if max_distance_from_target == 'r':
            print("Generating new data...")
            (total_df, sus_df) = EntitiesGenerator.generate_entities_paths(num_entities, num_tracks, False)
            continue

        try:
            res = rEF.locate_closest_entities_to_target(total_df, sus_df, float(max_distance_from_target))
            if not res:
                print("Data invalid or no path crosses were found! Generating new data...")
                (total_df, sus_df) = EntitiesGenerator.generate_entities_paths(num_entities, num_tracks, False)

        except ValueError as ex:
            print(ex)