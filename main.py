import pandas as pd
from RangedEntitiesFinder import ranged_entity_finder as rEF
import openpyxl

if __name__ == "__main__":
    # Reading data from Excel into DataFrames.
    total_df = pd.read_excel(r"data/dataTables.xlsx", "total", converters={"id": str})
    sus_df = pd.read_excel(r"data/dataTables.xlsx", "sus", converters={"id": str})

    # calcObj = rEF(total_df, sus_df)

    #(total_df, sus_df) = rEF.generate_data(5, 10, False)

    calcObj = rEF(total_df, sus_df)

    #print("test:", list(sus_df["id"])[0])

    rEF.generate_entities_paths()

    max_distance_from_target = input("Enter max distance from target in km (or enter 's' to stop the program): ")

    while max_distance_from_target != 's':
        if max_distance_from_target == 's': break

        try:
            calcObj.locate_closest_entities_to_target(float(max_distance_from_target))

        except ValueError as ex:
            print(ex)

        max_distance_from_target = input("\nEnter max distance from target in km (or enter 's' to stop the program): ")