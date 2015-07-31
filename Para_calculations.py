__author__ = 'mannsi'

import datetime

MALE = "M"
FEMALE = "F"


class Logic():
    def __init__(self,
                 event_list_csv,
                 min_requirement_csv,
                 world_champion_event_code,
                 npc_max_number_of_males,
                 npc_max_number_of_females,
                 total_number_of_males,
                 total_number_of_females):
        self.world_champion_event_code = world_champion_event_code
        self.npc_max_slots = {MALE: npc_max_number_of_males, FEMALE: npc_max_number_of_females}
        self.total_number_of_slots = {MALE: total_number_of_males, FEMALE: total_number_of_females}

        self.event_result_list = EventResultList(event_list_csv)
        self.min_requirement_list = MinimumRequirementList(min_requirement_csv)

        # Holds all npc swimmers who exceeded the max number of slots
        self.npcs_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npcs: slots}}
        self.npcs_non_capped_results = {MALE: {}, FEMALE: {}}  # {MALE: {npc: npc_slots}}

        # Holds extra rounding values when npcs are assigned swimmers. Used when all
        # npcs have gotten their slots but due to rounding some slots remain.
        self.npcs_rounded_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: rounded_value}}

        self._clean_csv_files()
        self._load_csv_files()
        self.world_champion_event_results = self._handle_world_champion_event()
        self._attach_minimum_requirements()
        self._remove_unqualified_results()

    def calculate_npc_numbers(self, gender):
        swimmers_and_weights = self.event_result_list.get_list_of_swimmers_and_max_weight()
        total_weight = Logic._get_weight_sum(swimmers_and_weights, gender)

        npcs = self.event_result_list.get_unique_npcs()
        npc_max_slots = self.npc_max_slots[gender]

        if len(npcs) == 0:
            raise Exception("Error, no NPCS found")

        for npc in npcs:
            num_npc_swimmers = sum([1 for x in swimmers_and_weights if x[0].gender == gender and x[0].npc == npc])
            npc_weight_sum = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender and x[0].npc == npc])
            npc_world_champion_slots = sum(
                [1 for x in self.world_champion_event_results
                 if x.swimmer.gender == gender and x.swimmer.npc == npc and x.rank <= 2])
            total_slots = self.total_number_of_slots[gender]
            weight_ratio = 0
            if total_weight > 0:
                weight_ratio = npc_weight_sum / total_weight
            npc_total_slots = total_slots * weight_ratio + npc_world_champion_slots
            if npc_total_slots > num_npc_swimmers:
                npc_total_slots = num_npc_swimmers

            if npc_total_slots <= int(npc_max_slots):
                rounded_value = npc_total_slots - int(npc_total_slots)
                self.npcs_rounded_results[gender][npc] = rounded_value
                self.npcs_non_capped_results[gender][npc] = int(npc_total_slots)

            elif npc_total_slots > npc_max_slots:
                self.npcs_rounded_results[gender].clear()
                self.npcs_non_capped_results[gender].clear()
                self.npcs_capped_results[gender][npc] = npc_max_slots
                self.event_result_list.remove_entire_npc()
                self.calculate_npc_numbers(gender)

        self._add_rounded_slots(gender)

        final_results = self.npcs_non_capped_results[gender].copy()
        final_results.update(self.npcs_capped_results[gender])
        return [(x[0], gender, x[1]) for x in final_results.items()]

    def _add_rounded_slots(self, gender):
        num_non_capped_slots = sum([result for result in self.npcs_non_capped_results[gender].values()])
        num_capped_slots = sum([capped_result for capped_result in self.npcs_capped_results[gender].values()])
        num_assigned_slots = num_non_capped_slots + num_capped_slots

        num_rounding_slots = self.total_number_of_slots[gender] - num_assigned_slots

        sorted_rounded_npc_list = self._get_sorted_rounded_list(gender)
        for i in range(num_rounding_slots):
            if len(sorted_rounded_npc_list) > 0:
                npc = sorted_rounded_npc_list.pop(0)
                # Skip over npcs that already have maximum number of slots
                while self.npcs_non_capped_results[gender][npc] == self.npc_max_slots[gender]:
                    npc = sorted_rounded_npc_list.pop(0)
                self.npcs_non_capped_results[gender][npc] += 1

    def _get_sorted_rounded_list(self, gender):
        # Convert dict to tuple list, sort tuple list and return list of npcs
        tuple_list = self.npcs_rounded_results[gender].items()
        sorted_tuple_list = sorted(tuple_list, key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_tuple_list]

    def _handle_world_champion_event(self):
        world_champion_event_results = self.event_result_list.get_single_event(self.world_champion_event_code)
        self.event_result_list.remove_single_event(self.world_champion_event_code)
        return world_champion_event_results

    @staticmethod
    def _get_weight_sum(swimmers_and_weights, gender):
        total_weight = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender])
        return total_weight

    def _clean_csv_files(self):
        # TODO
        # This will be implemented (if needed) once the real csv files are provided. Meant to fix any
        # issues between min_req_csv and event_list_csv
        pass

    def _load_csv_files(self):
        self.event_result_list.load_csv_file()
        self.min_requirement_list.load_csv_file()

    def _attach_minimum_requirements(self):
        self.event_result_list.attach_minimum_requirements(self.min_requirement_list)

    def _remove_unqualified_results(self):
        self.event_result_list.remove_unqualified_results()


class Swimmer():
    def __init__(self, swimmer_id, family_name, given_name, gender, birth_year, npc):
        self.id = swimmer_id
        self.family_name = family_name
        self.given_name = given_name
        self.gender = gender
        self.birth_year = birth_year
        self.npc = npc


class EventResult():
    def __init__(self,
                 event_code,
                 event,
                 swimmer_rank,
                 swimmer,
                 result_time,
                 event_date,
                 event_city,
                 event_country):
        self.event_code = event_code
        self.event = event
        self.rank = int(swimmer_rank)
        self.swimmer = swimmer
        self.result_time = result_time
        self.result_time_ms = self._time_to_ms(result_time)
        self.event_date = event_date
        self.event_city = event_city
        self.event_country = event_country
        self.minimum_requirement_time = datetime.timedelta()
        self.minimum_requirement_time_ms = 0
        self.weight = 0

        self._set_weight()

    def set_min_requirement_time(self, min_requirement_time):
        self.minimum_requirement_time = min_requirement_time
        self.minimum_requirement_time_ms = EventResult._time_to_ms(min_requirement_time)

    def _set_weight(self):
        if 1 <= self.rank <= 8:
            self.weight = 1
        elif 9 <= self.rank <= 12:
            self.weight = 0.8
        elif 13 <= self.rank <= 16:
            self.weight = 0.6
        elif 17 <= self.rank:
            self.weight = 0.5

    @staticmethod
    def _time_to_ms(time_string):
        split_time_string = time_string.replace(".", ":").split(":")

        if not len(split_time_string) == 3:
            raise Exception("Illegal time string: " + time_string)

        (mins, secs, ms) = split_time_string
        return int(
            datetime.timedelta(minutes=int(mins), seconds=int(secs), milliseconds=int(ms)).total_seconds() * 1000)


class EventResultList():
    def __init__(self, csv_file_content):
        self.csv_file_content = csv_file_content
        self.event_results = []

    def remove_entire_npc(self):


    def get_list_of_swimmers_and_max_weight(self):
        """
        Return a list of swimmers and their maximum weight as tuples
        """
        dict_of_swimmers_and_weight = {}
        for event_result in self.event_results:
            if event_result.swimmer.id not in dict_of_swimmers_and_weight:
                dict_of_swimmers_and_weight[event_result.swimmer.id] = (event_result.swimmer, event_result.weight)
            else:
                previous_swimmer_max_weight = dict_of_swimmers_and_weight.get(event_result.swimmer.id)[1]
                swimmer_max_weight = max(event_result.weight, previous_swimmer_max_weight)
                dict_of_swimmers_and_weight[event_result.swimmer.id] = (event_result.swimmer, swimmer_max_weight)

        return dict_of_swimmers_and_weight.values()

    def get_single_event(self, event_code):
        return [x for x in self.event_results if x.event_code == event_code]

    def remove_single_event_weights(self, event_code):
        for result in self.event_results:
            if result.event_code == event_code:
                result.weight = 0

    def load_csv_file(self):
        header_line_found = False

        for line in self.csv_file_content.splitlines():
            if header_line_found:
                self._add_csv_line(line)
            elif line.startswith("Event Code,Gender"):
                header_line_found = True

    def _add_csv_line(self, line):
        split_line = line.split(',')

        if len(split_line) != 14:
            raise Exception("Illegal event result csv line: '" + line + "'")

        swimmer = Swimmer(swimmer_id=split_line[4].strip(),
                          family_name=split_line[5].strip(),
                          given_name=split_line[6].strip(),
                          gender=split_line[1].strip(),
                          birth_year=split_line[8].strip(),
                          npc=split_line[7].strip())

        event_result = EventResult(
            event_code=split_line[0].strip(),
            swimmer=swimmer,
            event=split_line[2].strip(),
            swimmer_rank=split_line[3].strip(),
            result_time=split_line[9].strip(),
            event_date=split_line[11].strip(),
            event_city=split_line[12].strip(),
            event_country=split_line[13].strip()
        )
        self.event_results.append(event_result)

    def attach_minimum_requirements(self, minimum_requirement_list):
        for event_result in self.event_results:
            min_requirement = minimum_requirement_list.get_min_requirement(event_result.event)

            if not min_requirement:
                raise Exception("No minimum requirement found for event result: " + event_result.event)

            event_result.set_min_requirement_time(min_requirement.mqs)

    def nullify_unqualified_results(self):
        for result in self.event_results:
            if result.result_time_ms > result.minimum_requirement_time_ms:
                result.weight = 0

    def get_unique_npcs(self):
        return list(set([x.swimmer.npc for x in self.event_results]))  # Set is used to remove duplicates


class MinimumRequirement():
    def __init__(self, event, gender, mqs):
        self.event = event
        self.gender = gender
        self.mqs = mqs


class MinimumRequirementList():
    def __init__(self, csv_file_content):
        self.csv_file_content = csv_file_content
        self.min_requirements = []

    def load_csv_file(self):
        header_line_found = False

        for line in self.csv_file_content.splitlines():
            if header_line_found:
                self._add_csv_line(line)
            elif line.startswith('Event,Gender'):
                header_line_found = True

    def get_min_requirement(self, event):
        for min_requirement in self.min_requirements:
            if min_requirement.event == event:
                return min_requirement

    def _add_csv_line(self, line):
        split_line = line.split(",")

        if len(split_line) != 3:
            raise Exception("Illegal min requirement csv line: '" + line + "'")

        min_requirement = MinimumRequirement(event=split_line[0].strip(),
                                             gender=split_line[1].strip(),
                                             mqs=split_line[2].strip())
        self.min_requirements.append(min_requirement)
