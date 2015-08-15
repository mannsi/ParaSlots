__author__ = 'mannsi'

import datetime
import logging

MALE = "M"
FEMALE = "W"


class Logic:
    def __init__(self,
                 event_list_csv_list,
                 min_requirement_csv,
                 world_champion_event_code,
                 npc_max_number_of_males,
                 npc_max_number_of_females,
                 total_number_of_males,
                 total_number_of_females,
                 csv_separator):
        self._world_champion_event_results = []
        self.world_champion_event_codes = world_champion_event_code
        self.npc_max_slots = {MALE: npc_max_number_of_males, FEMALE: npc_max_number_of_females}

        # Holds all npc swimmers who exceeded the max number of slots
        self.npcs_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: Slots}}
        self.npcs_non_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: Slots}}

        # Holds extra rounding values when npcs are assigned swimmers. Used when all
        # npcs have gotten their slots but due to rounding some slots remain.
        self.npcs_rounded_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: rounded_value}}

        self._initialize_logging()
        logging.info("Starting Para Slots process")

        self.event_result_list = EventResultList(event_list_csv_list, csv_separator)
        self.event_result_list.load_csv_file()

        if min_requirement_csv:
            self.min_requirement_list = MinimumRequirementList(min_requirement_csv, csv_separator)
            self.min_requirement_list.load_csv_file()
            self._attach_minimum_requirements()
            self._nullify_unqualified_results()

        self._handle_world_champion_events()

        self._initial_total_number_of_slots = {MALE: total_number_of_males, FEMALE: total_number_of_females}
        self._total_number_of_slots = {MALE: total_number_of_males - self.get_number_of_wc_competitors(MALE),
                                       FEMALE: total_number_of_females - self.get_number_of_wc_competitors(FEMALE)}
        self._initial_npcs = self.event_result_list.get_unique_npcs(MALE)
        self._final_results = []  # list of Slot objects

    def get_number_of_wc_competitors(self, gender):
        world_champion_slots = sum(
            [1 for x in self._world_champion_event_results
             if x.swimmer.gender == gender and x.rank <= 2])
        return world_champion_slots

    def calculate_npcs_numbers(self):
        logging.info("Calculating npc male slots")
        logging.info("Total world champion slots for MALES", MALE,
                     sum([1 for x in self._world_champion_event_results if x.swimmer.gender == MALE and x.rank <= 2]))
        self._calculate_npc_by_gender(MALE)
        logging.info("Calculating npc female slots")
        logging.info("Total world champion slots for FEMALES", FEMALE,
                     sum([1 for x in self._world_champion_event_results if x.swimmer.gender == FEMALE and x.rank <= 2]))
        self._calculate_npc_by_gender(FEMALE)
        self._add_empty_npc_results()
        return self._final_results

    def _calculate_npc_by_gender(self, gender):
        swimmers_and_weights = self.event_result_list.get_list_of_swimmers_and_max_weight()
        total_weight = self._get_weight_sum(swimmers_and_weights, gender)

        npcs = self.event_result_list.get_unique_npcs(gender)
        npc_max_slots = self.npc_max_slots[gender]

        if len(npcs) == 0:
            logging.warning("Strange, no NPC found in calculation step")

        for npc in npcs:
            npc_weight_sum = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender and x[0].npc == npc])
            npc_world_champion_slots = sum(
                [1 for x in self._world_champion_event_results
                 if x.swimmer.gender == gender and x.swimmer.npc == npc and x.rank <= 2])
            total_slots = self._total_number_of_slots[gender]
            weight_ratio = 0
            if total_weight > 0:
                weight_ratio = npc_weight_sum / total_weight
            npc_calculated_slots = total_slots * weight_ratio
            npc_total_slots = npc_calculated_slots + npc_world_champion_slots

            slots = Slots(npc, gender, weight_percentage=npc_total_slots, wc_slots=npc_world_champion_slots)

            if npc_total_slots <= int(npc_max_slots):
                rounded_value = npc_total_slots - int(npc_total_slots)
                self.npcs_rounded_results[gender][npc] = rounded_value
                slots.calculated_slots = int(npc_calculated_slots)
                self.npcs_non_capped_results[gender][npc] = slots
                logging.info(
                    "- %s. %d slots (WC:%d,Calculated: %d). Ratio %.4f. Total slots being assigned: %d.",
                    npc, int(npc_total_slots), npc_world_champion_slots, npc_calculated_slots, weight_ratio, total_slots)

            elif npc_total_slots > npc_max_slots:
                self.npcs_rounded_results[gender].clear()
                self.npcs_non_capped_results[gender].clear()

                slots.calculated_slots = npc_max_slots - npc_world_champion_slots
                slots.capped = True
                self.npcs_capped_results[gender][npc] = slots
                self.event_result_list.remove_entire_npc(npc, gender)
                self._total_number_of_slots[gender] -= (npc_max_slots - npc_world_champion_slots)
                logging.info("- %s. %d slots. Ratio %.4f. CAPPED. Should have gotten %d slots without cap", npc,
                             npc_max_slots, weight_ratio, npc_total_slots)
                logging.info("  - Due to being capped all non-capped calculations will be repeated")
                self._calculate_npc_by_gender(gender)
                return

        self._add_rounded_slots(gender)

        results = self.npcs_non_capped_results[gender].copy()
        results.update(self.npcs_capped_results[gender])

        self._final_results += ([x[1] for x in results.items()])

    def _add_rounded_slots(self, gender):
        num_non_capped_slots = sum([result.total_slots() for result in self.npcs_non_capped_results[gender].values()])
        num_capped_slots = sum(
            [capped_result.total_slots() for capped_result in self.npcs_capped_results[gender].values()])
        num_assigned_slots = num_non_capped_slots + num_capped_slots

        num_rounding_slots = self._initial_total_number_of_slots[gender] - num_assigned_slots

        # TODO rounding slots is a negative numberr !!!!
        logging.info("Rounding for gender '%s'. num_non_capped_slots:%d. num_capped_slots: %d. num_assigned_slots: %d",
                     gender, num_non_capped_slots, num_capped_slots, num_assigned_slots)
        if num_rounding_slots > 0:
            logging.info("%d places need to be distributed due to rounding", num_rounding_slots)
        else:
            logging.info("No rounding places to distribute")

        sorted_rounded_npc_list = self._get_sorted_rounded_list(gender)
        for i in range(num_rounding_slots):
            if len(sorted_rounded_npc_list) > 0:
                npc = sorted_rounded_npc_list.pop(0)
                # Skip over npcs that already have maximum number of slots
                while self.npcs_non_capped_results[gender][npc] == self.npc_max_slots[gender]:
                    npc = sorted_rounded_npc_list.pop(0)
                logging.info("%s gets 1 slot for its rounding value %.3f", npc, self.npcs_rounded_results[gender][npc])

                self.npcs_non_capped_results[gender][npc].calculated_slots += 1

    def _get_sorted_rounded_list(self, gender):
        # Convert dict to tuple list, sort tuple list and return list of npcs
        tuple_list = self.npcs_rounded_results[gender].items()
        sorted_tuple_list = sorted(tuple_list, key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_tuple_list]

    def _handle_world_champion_events(self):
        logging.info(
            "Handle WC event (nullify 1/2 place swimmer weights since they already get slots for that placing)")
        for world_champion_event_code in self.world_champion_event_codes:
            self._world_champion_event_results.extend(
                self.event_result_list.get_single_event(world_champion_event_code))

        for wc_result in self._world_champion_event_results:
            if wc_result.rank <= 2:
                self.event_result_list.nullify_swimmer(wc_result.swimmer.id)

    @staticmethod
    def _get_weight_sum(swimmers_and_weights, gender):
        total_weight = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender])
        return total_weight

    def _attach_minimum_requirements(self):
        self.event_result_list.attach_minimum_requirements(self.min_requirement_list)

    def _nullify_unqualified_results(self):
        self.event_result_list.nullify_unqualified_results()

    def _add_empty_npc_results(self):
        for npc in self._initial_npcs:
            male_found = False
            female_found = False
            for result in self._final_results:
                if result.npc == npc and result.gender == MALE:
                    male_found = True
                if result.npc == npc and result.gender == FEMALE:
                    female_found = True
            if not male_found:
                self._final_results.append(Slots(npc, MALE, 0, 0))
            if not female_found:
                self._final_results.append(Slots(npc, FEMALE, 0, 0))

    @staticmethod
    def _initialize_logging():
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)


class Swimmer:
    def __init__(self, swimmer_id, family_name, given_name, gender, birth_year, npc):
        self.id = swimmer_id
        self.family_name = family_name
        self.given_name = given_name
        self.gender = gender
        self.birth_year = birth_year
        self.npc = npc


class EventResult:
    def __init__(self,
                 event_code,
                 event,
                 swimmer_rank,
                 swimmer,
                 result_time,
                 qualification,
                 event_date,
                 event_city,
                 event_country):
        self.event_code = event_code
        self.event = event
        self.rank = self.convert_rank(swimmer_rank)
        self.swimmer = swimmer
        self.result_time = result_time
        self.result_time_ms = self._time_to_ms(result_time)
        self.event_date = event_date
        self.event_city = event_city
        self.event_country = event_country
        self.minimum_requirement_time = datetime.timedelta()
        self.qualification = qualification
        self.minimum_requirement_time_ms = 0
        self.weight = 0

        self._set_weight()

    @staticmethod
    def from_csv_line(line, separator):
        # TODO check the new
        split_line = line.split(separator)

        if len(split_line) != 15:
            raise Exception("Illegal event result csv line: '" + line + "'")

        swimmer_id = split_line[4].strip()
        if not swimmer_id:
            return None

        swimmer = Swimmer(swimmer_id,
                          family_name=split_line[5].strip(),
                          given_name=split_line[6].strip(),
                          gender=split_line[1].strip(),
                          birth_year=split_line[8].strip(),
                          npc=split_line[7].strip())

        return EventResult(
            event_code=split_line[0].strip(),
            swimmer=swimmer,
            event=split_line[2].strip(),
            swimmer_rank=split_line[3].strip(),
            result_time=split_line[9].strip(),
            qualification=split_line[11].strip(),
            event_date=split_line[12].strip(),
            event_city=split_line[13].strip(),
            event_country=split_line[14].strip()
        )

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
        if not time_string:
            return 0

        split_time_string = time_string.replace(".", ":").split(":")

        if not len(split_time_string) == 3:
            raise Exception("Illegal time string: " + time_string)

        (mins, secs, ms) = split_time_string
        return int(
            datetime.timedelta(minutes=int(mins), seconds=int(secs), milliseconds=int(ms)).total_seconds() * 1000)

    @staticmethod
    def convert_rank(swimmer_rank):
        # Filter out non numeric characters
        sanitized_list = [x for x in swimmer_rank if x.isdigit()]
        return int(''.join(sanitized_list))


class EventResultList:
    def __init__(self, csv_file_content_list, csv_separator):
        self.csv_file_content_list = csv_file_content_list
        self.event_results = []
        self.csv_separator = csv_separator

    def remove_entire_npc(self, npc, gender):
        others = [x for x in self.event_results if x.swimmer.npc != npc or x.swimmer.gender != gender]
        self.event_results = others


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

    def load_csv_file(self):
        logging.info("Loading event lines")
        header_line_found = False

        for line in self.csv_file_content_list:
            if header_line_found:
                self._add_csv_line(line)
            elif line.startswith("Event Code%sGender" % self.csv_separator):
                header_line_found = True
        logging.info("=> %d event lines loaded" % len(self.event_results))

    def _add_csv_line(self, line):
        event_result = EventResult.from_csv_line(line, self.csv_separator)
        if not event_result or not event_result.swimmer.id:
            return
        if event_result.qualification in ("MQS", ""):
            self.event_results.append(event_result)

    def attach_minimum_requirements(self, minimum_requirement_list):
        for event_result in self.event_results:
            min_requirement = minimum_requirement_list.get_min_requirement(event_result.event)

            if not min_requirement:
                raise Exception("No minimum requirement found for event result: " + event_result.event)

            event_result.set_min_requirement_time(min_requirement.minimum_time)

    def nullify_unqualified_results(self):
        logging.info("Nullifying event result lines with times below msq times")
        counter = 0
        for result in self.event_results:
            if result.result_time_ms > result.minimum_requirement_time_ms:
                result.weight = 0
                counter += 1
        logging.info("=> %d lines nullified" % counter)

    def get_unique_npcs(self, gender):
        return sorted(list(set([x.swimmer.npc for x in self.event_results if
                                x.swimmer.gender == gender])))  # Set is used to remove duplicates

    def nullify_swimmer(self, swimmer_id):
        for result in self.event_results:
            if result.swimmer.id == swimmer_id:
                result.weight = 0


class MinimumRequirement:
    def __init__(self, event, gender, minimum_time):
        self.event = event
        self.gender = gender
        self.minimum_time = minimum_time

    @staticmethod
    def from_csv_line(line, separator):
        split_line = line.split(separator)

        if len(split_line) != 3:
            raise Exception("Illegal min requirement csv line: '" + line + "'")

        return MinimumRequirement(event=split_line[0].strip(),
                                  gender=split_line[1].strip(),
                                  minimum_time=split_line[2].strip())


class MinimumRequirementList:
    def __init__(self, csv_file_content, csv_separator):
        self.csv_file_content_lines = csv_file_content
        self.min_requirements = []
        self.csv_separator = csv_separator

    def load_csv_file(self):
        logging.info("Loading minimum requirements csv lines")
        header_line_found = False

        for line in self.csv_file_content_lines:
            if header_line_found:
                self._add_csv_line(line)
            elif line.startswith('Event,Gender'):
                header_line_found = True
        logging.info("=> %d minimum requirement lines loaded" % len(self.min_requirements))

    def get_min_requirement(self, event):
        for min_requirement in self.min_requirements:
            if min_requirement.event == event:
                return min_requirement

    def _add_csv_line(self, line):
        min_requirement = MinimumRequirement.from_csv_line(line, self.csv_separator)
        self.min_requirements.append(min_requirement)


class Slots:
    def __init__(self, npc, gender, weight_percentage, wc_slots, capped=False):
        self.npc = npc
        self.gender = gender
        self.weight_percentage = weight_percentage
        self.wc_slots = wc_slots
        self.calculated_slots = 0
        self.capped = capped

    def total_slots(self):
        return self.wc_slots + self.calculated_slots
