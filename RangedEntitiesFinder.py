import multiprocessing
import threading
import time

from fontTools.unicodedata import block
from geopy import distance as gpy_distance
import pandas as pd
import math
import numpy as np
from datetime import datetime, timedelta
import random as rand
import matplotlib
import matplotlib.pyplot as plt

class ranged_entity_finder():
    display_fig = plt.figure(1)
    plotter = display_fig.add_subplot(111, projection="3d")

    '''
    Calculates the distance between two gives given points
    on Earth. Each points consists of three values,
    Latitude, Longitude, and height above the surface (in km).
    '''
    @staticmethod
    def _calc_distance(point_origin: tuple, point_destination: tuple) -> float:
        if point_origin == point_destination: return 0

        # Saving the latitude and longitude coordinates separately.
        horiz_coords_origin = (point_origin[0], point_origin[1])
        horiz_coords_destination = (point_destination[0], point_destination[1])

        # Calculting the distance between the latitude and longitude coordinates.
        horiz_distance = gpy_distance.geodesic(
            horiz_coords_origin,
            horiz_coords_destination).km

        # Calculating the height difference between the points.
        vert_distance = point_destination[2] - point_origin[2]

        # Applying pythagoras theorem to calculate the distance between the two points.
        return math.sqrt(horiz_distance**2 + vert_distance**2)

    '''
    Rounds the coordinates in the tuple to 3 places after decimal point.
    '''
    @staticmethod
    def _round_coordinates(point_to_round: tuple, places_after_decimal: int = 3):
        if places_after_decimal <= 0: places_after_decimal = 3

        return (round(point_to_round[0], places_after_decimal),
                round(point_to_round[1], places_after_decimal),
                round(point_to_round[2], places_after_decimal))


    '''
    Locates the closest entities within a defined distance from the **sus**picious target.
    The distance is measured in km.
    
    total_df:   DataFrame that contains data about the path of entities including a target.
    sus_df:     DataFrame that contains data about the path of the target.
    '''
    @staticmethod
    def locate_closest_entities_to_target(total_df: pd.DataFrame, sus_df: pd.DataFrame, distance_from_target = 1000.0) -> bool:
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

        # Saving occurrences of entities crossing paths with the target without timestamp relation.
        # Grouping according to timestamps is done later.
        path_crosses = non_target_entities.merge(
            sus_df[["lat", "long", "height"]],
            on=["lat", "long", "height"])

        # Checking if any cross paths exist.
        if path_crosses.empty:
            print("No entities crossed paths with target!")
            return False

        # Grouping the path crosses according to timestamps (by rising order), latitude, longitude, and height.
        path_crosses_grouped = path_crosses.groupby(by=["ts", "lat", "long", "height"])[["id"]].apply(dict).dropna()
        # Storing the coordinates (as points) as a Series of dictionary of tuples, stored in sus DataFrame.
        path_points_sus = sus_df.groupby(by=["ts"])[["lat", "long", "height"]].apply(dict)

        print("Format of coordinates: (latitude [deg], longitude [deg], height [km])\n")

        # Iterating over the path of the target entity.
        for current_ts in path_points_sus.keys():
            if current_ts not in path_crosses_grouped.index: continue

            # The current group of entities (except target) in the current timestamp.
            ts_group = path_crosses_grouped.loc[current_ts]

            # The current location of the target entity (sus).
            # path_points_sus[current_ts].values() gives a series of values where the left number
            # is an index and the right is the actual value that's needed.
            # val.values[0] gets the needed value.
            sus_location = tuple(float(val.values[0]) for val in path_points_sus[current_ts].values())

            # Previous timestamp is used for checking if the current timestamp was printed already.
            prev_ts = math.nan

            # Iterating over the group of entities which belong to the current timestamp.
            for current_entities in ts_group.items():
                distance_calculated = ranged_entity_finder._calc_distance(sus_location, current_entities[0])

                if distance_calculated >= distance_from_target: continue

                if prev_ts != current_ts:
                    print(f"---------- Timestamp {current_ts} ----------")
                    prev_ts = current_ts

                # Rounding the coordinate values of the entities (both that are close to target and of target itself).
                # Used purely for printing.
                entities_location_rounded = ranged_entity_finder._round_coordinates(current_entities[0])
                sus_location_rounded = ranged_entity_finder._round_coordinates(sus_location)

                print(f"Entity(ies):", end=' ')

                # Note2self: asterisk before an iterable object (such as a list)
                #            in a print statement will print all the values in an object
                #            in a readable way. Example: [1, 2, 3] with sep=", "
                #            will be printed as: 1, 2, 3    
                # Function .values() created a Pandas Series which is turned into a list.
                # The [0] is used to read only the Ids of the entities, without the idexes of the series.
                print(*list(current_entities[1].values())[0], sep=", ", end=' ')
                print(f"is/are close to target ({round(distance_calculated, 3)} km)!\n" 
                    + f"Entity(ies) coordinates:\t{entities_location_rounded}\nTarget coordinates:\t\t{sus_location_rounded}\n")

        ranged_entity_finder.update_figure(non_target_entities, sus_df)

        return True

    '''
    Generates a path of an entity that doesn't cross paths with sus.
    '''
    @staticmethod
    def _generate_entity_path(entity_num: int, num_tracks: int) -> pd.DataFrame:
        entity_idx = entity_num - 1

        # Generating data
        data = {
            "id": np.repeat(entity_num, num_tracks),
            "ts": timestamps,
            "lat":
                starting_positions[entity_idx, 0] + lat_increments[entity_idx] *
                np.arange(num_tracks),
            "long":
                starting_positions[entity_idx, 1] + long_increments[entity_idx] *
                np.arange(num_tracks),
            "height":
                starting_heights[entity_idx] + height_increments[entity_idx] *
                np.arange(num_tracks)
        }

        return pd.DataFrame(data)


    '''
    Generates a path of an entity that crosses paths with a target entity.
    '''
    @staticmethod
    def _generate_entity_with_target_cross_path(entity_num: int, sus_num: int, num_tracks: int) -> pd.DataFrame:
        # Calculating indexes of entities for easier data access.
        entity_idx = entity_num - 1
        #sus_idx = sus_num - 1

        # Selecting a random timestamp (ts_of_cross_path) from an index (ts_idx_of_cross_path)
        # to be a time when a cross path occurs.
        ts_idx_of_cross_path = rand.randint(0, num_tracks - 1)
        ts_of_cross_path = timestamps[ts_idx_of_cross_path]

        # The row in the DataFrame that contains that data about the entity (such as location) at the time when crossing paths.
        sus_data_at_ts = sus_path[(sus_path["id"] == sus_num) & (sus_path["ts"] == ts_of_cross_path)]

        # Getting the index of sus from the DataFrame.
        sus_idx_in_df = sus_data_at_ts.index[0]

        # .loc is used to make sure the tuple contains only np.float values and not Pandas Series.
        cross_path_location = (sus_data_at_ts.loc[sus_idx_in_df, "lat"],
                               sus_data_at_ts.loc[sus_idx_in_df, "long"],
                               sus_data_at_ts.loc[sus_idx_in_df, "height"])

        cross_path_idx_of_entity = rand.randint(0, num_tracks - 1)

        entity_starting_location = (starting_positions[entity_idx, 0],
                                    starting_positions[entity_idx, 1],
                                    starting_heights[entity_idx])

        '''
        Calculating the lat, long and height increments required to reach the cross path location at the timestamp
        specified in relation to the beginning.
        Example: an entity starts at the 1st timestamp, and the cross paths is at the 5th.
                 Starting location of entity: (12, 18, 30)
                 Cross paths location:        (15, 6, 29.1)
                 Between the 1st timestamp and 5th there are 3 timestamps, 2nd, 3rd, and 4th timestamps.
                 Because of this, there are 3 increments between the starting position and cross paths.
                 Meaning that the increments will be:
                 1. lat:    |12 - 15| * 1 = 3
                 2. long:   |18 - 6| * (-1) = -4
                 3. height: |30 - 29.1| * (-1) = -0.3
                 Note that if the starting location value of the current axis is bigger than
                 the value in the same axis of the cross paths location, the increment will be negative
                 (absolute value multiplied by -1).
                 Using the entity index minus -1 gives the amount of timestamps in between the start and end. 
        '''
        #region Increments Calculation
        # Calculating the coordinate differences on each axis.
        lat_new_increment = math.fabs(entity_starting_location[0] - cross_path_location[0])

        long_new_increment = math.fabs(entity_starting_location[1] - cross_path_location[1])

        height_new_increment = math.fabs(entity_starting_location[2] - cross_path_location[2])

        # Calculating the amount of timestamps between the beginning and cross paths.
        ts_between_amount = cross_path_idx_of_entity - 1

        # Calculating the increments given that the amount of timestamps between beginning and
        # cross paths is larger than zero. Otherwise, the increments are straight from beginning to end.
        if ts_between_amount > 0:
            lat_new_increment /= ts_between_amount
            long_new_increment /= ts_between_amount
            height_new_increment /= ts_between_amount

        # Verifying the sign of each increment is correct.
        if entity_starting_location[0] > cross_path_location[0]: lat_new_increment *= -1

        if entity_starting_location[1] > cross_path_location[1]: long_new_increment *= -1

        if entity_starting_location[2] > cross_path_location[2]: height_new_increment *= -1
        #endregion

        # Generating the rest of the positions of timestamps that connect between the beginning to the cross paths,
        # and all the way to the end of the path of the entity.
        #for current_location_multiplier in range(2, num_tracks):
        entity_path = {
            "id": np.repeat(entity_num, num_tracks),
            "ts": timestamps,
            "lat":
                starting_positions[entity_idx, 0] + lat_new_increment *
                np.arange(num_tracks),
            "long":
                starting_positions[entity_idx, 1] + long_new_increment *
                np.arange(num_tracks),
            "height":
                starting_heights[entity_idx] + height_new_increment *
                np.arange(num_tracks)
        }

        return pd.DataFrame(entity_path)


    '''
    Generates paths of entities based on the amount of tracks (timestamps).
    Some entities cross paths with a suspicious target (sus).
    '''
    @staticmethod
    def generate_entities_paths(num_entities: int = 5, num_tracks: int = 10, rand_sus_num: bool = False):
        # Making variables global to reduce amount of function arguments of those being called from this function.
        global sus_path, timestamps, starting_positions, starting_heights, lat_increments, long_increments, height_increments

        # Generate a single set of timestamps
        timestamps = [datetime.now() + timedelta(seconds=i) for i in range(num_tracks)]

        # Initialize starting positions and linear increments
        # The defined increments (lat_increments, long_increments, height_increments)
        # are the default increments when an entity does not cross paths with the target (sus).
        starting_positions  = np.random.uniform(low=-90.0, high=90.0, size=(num_entities, 2))   # Starting lat and long
        starting_heights    = np.random.uniform(low=0.0, high=100.0, size=num_entities)         # Starting height
        lat_increments      = np.random.uniform(low=-0.1, high=0.1, size=num_entities)          # Lat change per step
        long_increments     = np.random.uniform(low=-0.1, high=0.1, size=num_entities)          # Long change per step
        height_increments   = np.random.uniform(low=-10.0, high=10.0, size=num_entities)        # Height change per step

        # Giving an initial value to the target entity, as it might not be randomized.
        sus_num = 1

        # Randomizing the sus target.
        if rand_sus_num and num_entities > 1:
            sus_num = rand.randint(2, num_entities)

        # Generating the path of the target entity.
        sus_path = ranged_entity_finder._generate_entity_path(sus_num, num_tracks)

        # Initializing a DataFrame that stores all the data of the entities (including the target).
        all_entities = pd.DataFrame()

        for current_entity_num in range(1, num_entities):
            if current_entity_num == sus_num:
                # Adding the sus target to the DataFrame with all entities.
                all_entities = pd.concat([all_entities, sus_path]).reset_index(drop=True)
                continue

            # Making random entities cross paths with the target.
            cross_paths_with_target = bool(rand.randint(0, 1))

            if cross_paths_with_target:
                new_entity_data = ranged_entity_finder._generate_entity_with_target_cross_path(current_entity_num, sus_num, num_tracks)

            else: new_entity_data = ranged_entity_finder._generate_entity_path(current_entity_num, num_tracks)

            all_entities = pd.concat([all_entities, new_entity_data]).reset_index(drop=True)

        # Rounding coordinate data as a result of an issue that has to do with Pandas's merge function,
        # which has a precision issue with float numbers with many digits (code failed with 6, didn't test 5) after the decimal place.
        all_entities[['lat', 'long', 'height']] = all_entities[['lat', 'long', 'height']].round(4)
        sus_path[['lat', 'long', 'height']] = sus_path[['lat', 'long', 'height']].round(4)

        # Returning DataFrames in a tuple.
        return (all_entities, sus_path)

    '''
    Used for displaying the paths of entities in 3D.
    Uses X, Y, Z axis instead of showing the paths around Earth
    to make things simpler.
    '''
    @staticmethod
    def update_figure(all_entities: pd.DataFrame, sus_entity: pd.DataFrame):
        #ranged_entity_finder.display_fig.clf()

        #ranged_entity_finder.display_fig = plt.figure()

        # Latitude in this code is considered to be X axis.
        # Longitude in this code is considered to be Y axis.
        # Height in this code is considered to be Z axis.

        # Non target coordinates.
        lat_values = all_entities["lat"]
        long_values = all_entities["long"]
        height_values = all_entities["height"]

        # Target coordinates.
        sus_lats = sus_entity["lat"]
        sus_longs = sus_entity["long"]
        sus_heights = sus_entity["height"]

        # Plotting data of entities which aren't the target.
        ranged_entity_finder.plotter.scatter(lat_values, long_values, height_values)
        # Plotting data of the target entity.
        ranged_entity_finder.plotter.scatter(sus_lats, sus_longs, sus_heights)

        # todo: find out why show doesn't work a second time after closing the figure window.
        plt.show()