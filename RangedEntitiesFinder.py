from geopy import distance as gpy_distance
import pandas as pd
import math
import matplotlib.pyplot as plt

class RangedEntitiesFinder:
    """
    Used to find entities within range of a specific target.
    """

    display_fig = plt.figure(1)
    plotter = display_fig.add_subplot(111, projection="3d")

    @staticmethod
    def _calc_distance(point_a: tuple, point_b: tuple) -> float:
        """
        Calculates the distance between two gives given points
        on Earth. Each points consists of three values,
        Latitude, Longitude, and height above the surface (in km).

        :param point_a: the first point.
        :param point_b: the second point.
        :return: the distance between the two points on Earth.
        """

        if point_a == point_b: return 0

        # Saving the latitude and longitude coordinates separately.
        horiz_coords_origin = (point_a[0], point_a[1])
        horiz_coords_destination = (point_b[0], point_b[1])

        # Calculating the distance between the latitude and longitude coordinates.
        horiz_distance = gpy_distance.geodesic(
            horiz_coords_origin,
            horiz_coords_destination).km

        # Calculating the height difference between the points.
        vert_distance = point_b[2] - point_a[2]

        # Applying pythagoras theorem to calculate the distance between the two points.
        return math.sqrt(horiz_distance**2 + vert_distance**2)


    @staticmethod
    def _round_coordinates(point_to_round: tuple, places_after_decimal: int = 3):
        """
        Rounds the coordinates in the tuple to 3 places after decimal point.

        :param point_to_round: the point to round the values of.
        :param places_after_decimal: the rounding accuracy.
        :return: the point with rounded values.
        """

        if places_after_decimal <= 0: places_after_decimal = 3

        return (round(point_to_round[0], places_after_decimal),
                round(point_to_round[1], places_after_decimal),
                round(point_to_round[2], places_after_decimal))

    @staticmethod
    def locate_closest_entities_to_target(total_df: pd.DataFrame, sus_df: pd.DataFrame, distance_from_target = 1000.0) -> bool:
        """
        Locates the closest entities within a defined distance from the **sus**picious target.
        The distance is measured in km.

        :param total_df: DataFrame that contains data about the path of entities including a target.
        :param sus_df: DataFrame that contains data about the path of the target.
        :param distance_from_target: the maximum distance from the target allowed.
        :return: True if a non target entity was found close to the suspicious target entity. Otherwise, False.
        """

        # Checking if distance is valid.
        if distance_from_target <= 0: 
            print("Max distance can't be smaller or equal to 0!")
            return False

        # Finding the target ID to drop from total_df for easier navigation in the data.
        entity_id_to_filter = list(sus_df["id"])[0]

        # Validating sus table.
        if all(sus_df["id"] != entity_id_to_filter):
            print("Sus table is invalid!")
            return False

        # Removing (dropping) the data about the target from total_df to make working with the data easier.
        # The target might have been dropped since a previous user input during runtime.
        non_target_entities = total_df[total_df["id"] != entity_id_to_filter]

        # Grouping according to timestamps.
        # Storing ID, lat, long, and height columns in the new grouped DataFrame.
        # When reading data according to each timestamp, the mentioned columns (ID, lat, long, height) will
        # have values as Pandas Series.
        paths_of_ts = (non_target_entities.groupby(by="ts")[["id", "lat", "long", "height"]]).apply(pd.DataFrame)

        # Storing the coordinates (as points) as a Series of dictionary of tuples, stored in sus DataFrame.
        path_points_sus = sus_df.groupby(by=["ts"])[["lat", "long", "height"]].apply(dict)

        print("Format of coordinates: (latitude [deg], longitude [deg], height [km])\n")

        # Iterating over the path of the target entity.
        for current_ts in path_points_sus.keys():
            if current_ts not in paths_of_ts.index: continue

            # The current group of entities (except target) in the current timestamp.
            entity_ts_group = paths_of_ts.loc[current_ts]
            # The current location of the target entity (sus).
            # path_points_sus[current_ts].values() gives a series of values where the left number
            # is an index and the right is the actual value that's needed.
            # val.values[0] gets the needed value.
            sus_location = tuple(float(val.values[0]) for val in path_points_sus[current_ts].values())
            # Previous timestamp is used for checking if the current timestamp was printed already.
            prev_ts = math.nan

            # Iterating over the group of entities which belong to the current timestamp.
            for current_entity in entity_ts_group.iterrows():
                # current_entity[1] gets the Pandas Series stored in the tuple of the current entity.
                # Series structure: id, lat, long, height.
                # [1:] slices the series to read the lat, long, and height coordinates.
                entity_location = tuple(current_entity[1][1:])

                distance_calculated = RangedEntitiesFinder._calc_distance(sus_location, entity_location)

                print("Distance calculated:", distance_calculated, "[km]")

                if distance_calculated >= distance_from_target: continue

                if prev_ts != current_ts:
                    print(f"---------- Timestamp {current_ts} ----------")
                    prev_ts = current_ts

                # Rounding the coordinate values of the entities (both that are close to target and of target itself).
                # Used purely for printing.
                entities_location_rounded = RangedEntitiesFinder._round_coordinates(entity_location)
                sus_location_rounded = RangedEntitiesFinder._round_coordinates(sus_location)

                print(f"Entity(ies):", end=' ')

                # Note2self: asterisk before an iterable object (such as a list)
                #            in a print statement will print all the values in an object
                #            in a readable way. Example: [1, 2, 3] with sep=", "
                #            will be printed as: 1, 2, 3    
                # Function .values() created a Pandas Series which is turned into a list.
                # The [0] is used to read only the Ids of the entities, without the indexes of the series.
                print(*list(current_entity), sep=", ", end=' ')
                print(f"is/are close to target ({round(distance_calculated, 3)} km)!\n" 
                    + f"Entity(ies) coordinates:\t{entities_location_rounded}\nTarget coordinates:\t\t{sus_location_rounded}\n")

        RangedEntitiesFinder.update_figure(non_target_entities, sus_df)

        return True

    @staticmethod
    def update_figure(all_entities: pd.DataFrame, sus_entity: pd.DataFrame):
        """
        Used for displaying the paths of entities in 3D.
        Uses X, Y, Z axis instead of showing the paths around Earth
        to make things simpler.

        Note: Latitude in this code is considered to be X axis.
              Longitude in this code is considered to be Y axis.
              Height in this code is considered to be Z axis.
        :param all_entities:
        :param sus_entity:
        :return:
        """

        # Non target coordinates.
        lat_values = all_entities["lat"]
        long_values = all_entities["long"]
        height_values = all_entities["height"]

        # Target coordinates.
        sus_lats = sus_entity["lat"]
        sus_longs = sus_entity["long"]
        sus_heights = sus_entity["height"]

        plt.xlabel("Latitude")
        plt.ylabel("Longitude")

        # Plotting data of entities which aren't the target.
        RangedEntitiesFinder.plotter.scatter(lat_values, long_values, height_values)
        # Plotting data of the target entity.
        RangedEntitiesFinder.plotter.scatter(sus_lats, sus_longs, sus_heights)

        # todo: find out why show doesn't work a second time after closing the figure window.
        plt.show()