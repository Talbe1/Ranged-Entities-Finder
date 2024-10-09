from geopy import distance as gpy_distance
import pandas as pd
import math
import numpy as np
from datetime import datetime, timedelta
import random as rand

class ranged_entity_finder():
    total_df = pd.DataFrame # DataFrame that contains data about the path of entities including a target.
    sus_df = pd.DataFrame   # DataFrame that contains data about the path of the target.

    def __init__(self, total: pd.DataFrame, sus: pd.DataFrame):
        if total.shape[1] != 5 or sus.shape[1] != 5:
            raise ValueError("Table dimensions are incorrect!")

        self.total_df = total
        self.sus_df = sus

    '''
    Calculates the distance between two gives given points
    on Earth. Each points consists of three values,
    Latitude, Longitude, and height above the surface (in km).
    '''
    def _calc_distance(self, point_origin: tuple, point_destination: tuple) -> float:
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

        # Applying pythagoras theorm to calculate the distance between the two points.
        return math.sqrt(horiz_distance**2 + vert_distance**2)


    '''
    Locates the closest entities within a defined distance from the **sus**picious target.
    The distance is measured in km.
    '''
    def locate_closest_entities_to_target(self, distance_from_target = 1000.0) -> None:
        # Checking if distance is valid.
        if distance_from_target <= 0: 
            print("Max distance can't be smaller or equal to 0!")
            return

        # Finding the target Id to drop from total_df for easier navigation in the data.
        entity_id_to_filter = list(self.sus_df["id"])[0]

        # Validating sus table.
        if all(self.sus_df["id"] != entity_id_to_filter):
            print("Sus table is invalid!")
            return

        # Removing (dropping) the data about the target from total_df to make working with the data easier.
        # The target might had been dropped since a previous user input during runtime.
        self.total_df = self.total_df[self.total_df["id"] != entity_id_to_filter]

        
        # Saving occurences of entities crossing paths with the target without timestamp relation.
        # Grouping according to timestamps is done later.
        path_crosses = self.total_df.merge(
            self.sus_df[["lat", "long", "height"]],
            on=["lat", "long", "height"])

        # Grouping the path crosses according to timestamps (by rising order), latitude, longitude, and height.
        path_crosses_grouped = path_crosses.groupby(by=["ts", "lat", "long", "height"])[["id"]].apply(dict).dropna()
        
        # Storing the coordinates (as points) as a Series of dictionary of tuples, stored in sus DataFrame.
        path_points_sus = self.sus_df.groupby(by=["ts"])[["lat", "long", "height"]].apply(dict)
        print("total:", self.total_df)
        print("sus:", self.sus_df)

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

            # Previou timestamp is used for checking if the current timestamp was printed already.
            prev_ts = math.nan

            # Iterating over the group of entities which belong to the current timestamp.
            for current_entities in ts_group.items():
                distance_calculated = self._calc_distance(sus_location, current_entities[0])

                if distance_calculated >= distance_from_target: continue

                if prev_ts != current_ts:
                    print(f"---------- Timestamp {current_ts} ----------")
                    prev_ts = current_ts

                print(f"Entity(ies):", end=' ')

                # Note2self: asterisk before an iterable object (such as a list)
                #            in a print statement will print all the values in an object
                #            in a readable way. Example: [1, 2, 3] with sep=", "
                #            will be printed as: 1, 2, 3    
                # Function .values() created a Pandas Series which is turned into a list.
                # The [0] is used to read only the Ids of the entities, without the idexes of the series.
                print(*list(current_entities[1].values())[0], sep=", ", end=' ')
                print(f"is/are close to target ({round(distance_calculated, 3)} km)!\n" 
                    + f"Entity(ies) coordinates:\t{current_entities[0]}\nTarget coordinates:\t\t{sus_location}\n")


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

    @staticmethod
    def _generate_entity_with_target_cross_path(entity_num: int, sus_num: int, time_of_sus: datetime, num_tracks: int) -> pd.DataFrame:
        entity_idx = entity_num - 1
        sus_idx = sus_num - 1

        sus_at_time = sus_path[sus_path["id"] == sus_num and sus_path["ts"] == time_of_sus]

        sus_location_at_time = (sus_at_time["lat"], sus_at_time["long"], sus_at_time["height"])

    @staticmethod
    def generate_entities_paths(num_entities: int = 5, num_tracks: int = 10, rand_sus_num: bool = False):
        # Making variables global to reduce amount of function arguments of those being called from this function.
        global sus_path, timestamps, starting_positions, starting_heights, lat_increments, long_increments, height_increments

        # Generate a single set of timestamps
        timestamps = [datetime.now() + timedelta(seconds=i) for i in range(num_tracks)]

        # Initialize starting positions and linear increments
        starting_positions  = np.random.uniform(low=-90.0, high=90.0, size=(num_entities, 2))   # Starting lat and long
        starting_heights    = np.random.uniform(low=0.0, high=10000.0, size=num_entities)       # Starting height
        lat_increments      = np.random.uniform(low=-0.1, high=0.1, size=num_entities)          # Lat change per step
        long_increments     = np.random.uniform(low=-0.1, high=0.1, size=num_entities)          # Long change per step
        height_increments   = np.random.uniform(low=-10.0, high=10.0, size=num_entities)        # Height change per step

        sus_num = 1

        if rand_sus_num and num_entities > 1:
            sus_num = rand.randint(2, num_entities)

        sus_path = ranged_entity_finder._generate_entity_path(sus_num, num_tracks)

        for current_entity_num in range(1, num_entities):
            cross_paths_with_target = bool(rand.randint(0, 1))

            if cross_paths_with_target:
                ranged_entity_finder._generate_entity_with_target_cross_path(current_entity_num, sus_num, ) #todo: continue here

    @staticmethod
    def generate_data(num_entities: int = 5, num_tracks: int = 10, rand_num_tracks: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
        if rand_num_tracks:
            num_tracks = rand.randint(int(num_tracks / 2), num_tracks)

        # Generate a single set of timestamps
        timestamps = [datetime.now() + timedelta(seconds=i) for i in range(num_tracks)]

        # Initialize starting positions and linear increments
        start_positions     = np.random.uniform(low=-90.0, high=90.0, size=(num_entities, 2))   # Starting lat and long
        height_starts       = np.random.uniform(low=0.0, high=10000.0, size=num_entities)       # Starting height
        lat_increment       = np.random.uniform(low=-0.1, high=0.1, size=num_entities)          # Lat change per step
        long_increment      = np.random.uniform(low=-0.1, high=0.1, size=num_entities)          # Long change per step
        height_increment    = np.random.uniform(low=-10.0, high=10.0, size=num_entities)        # Height change per step

        # Generate data
        data = {
            "id": np.repeat(np.arange(1, num_entities + 1), num_tracks),
            "ts": np.tile(timestamps, num_entities),
            "lat": np.concatenate([
                start_positions[i, 0] + lat_increment[i] * 
                np.arange(num_tracks) for i in range(num_entities)
            ]),
            "long": np.concatenate([
                start_positions[i, 1] + long_increment[i] * 
                np.arange(num_tracks) for i in range(num_entities)
            ]),
            "height": np.concatenate([
                height_starts[i] + height_increment[i] * 
                np.arange(num_tracks) for i in range(num_entities)
            ])
        }

        data = pd.DataFrame(data)

        entity_ids = list(data.groupby(by="id").groups)

        entity_idx_to_be_target = rand.randint(0, len(entity_ids) - 1)
        
        sus_path = data[data["id"] == entity_ids[entity_idx_to_be_target]]

        entities_path = data[data["id"] != entity_ids[entity_idx_to_be_target]]
        print("data:", data.groupby(["lat", "long", "height"]).apply(pd.DataFrame), "\n\n\n\n")

        #print(sus_path)
        # Create DataFrame and return
        return (entities_path, sus_path)