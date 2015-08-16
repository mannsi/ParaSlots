__author__ = 'mannsi'

import datetime
import logging

MALE = "M"
FEMALE = "W"


class Logic:
    def __init__(self,
                 event_list_csv_list,
                 min_requirement_csv_list,
                 world_champion_event_code,
                 npc_max_number_of_males,
                 npc_max_number_of_females,
                 total_number_of_males,
                 total_number_of_females,
                 csv_separator):
        self._world_champion_event_results = []
        self._world_champion_event_codes = world_champion_event_code
        self._npc_max_slots = {MALE: npc_max_number_of_males, FEMALE: npc_max_number_of_females}
        self._total_number_of_slots = {MALE: total_number_of_males, FEMALE: total_number_of_females}

        # Holds all npc swimmers who exceeded the max number of slots
        self.npcs_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: Slots}}

        self.npcs_non_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: Slots}}

        # Holds extra rounding values when npcs are assigned swimmers. Used when all
        # npcs have gotten their slots but due to rounding some slots remain.
        self.npcs_rounded_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: rounded_value}}

        self._final_results = []  # list of Slot objects

        self._remaining_number_of_slots = {MALE: 0, FEMALE: 0}  # Total # of slots - WC slots - capped slots

        self._initialize_logging()
        logging.info("Starting Para Slots process")

        self._initial_data_setup(event_list_csv_list, min_requirement_csv_list, csv_separator)

    def calculate_npcs_numbers(self):
        logging.info("CALCULATING NPC MALE SLOTS")
        self._calculate_npc_by_gender(MALE)

        logging.info("CALCULATING NPC FEMALE SLOTS")
        self._calculate_npc_by_gender(FEMALE)
        return self._final_results

    def _add_non_capped_slot(self, gender, npc, npc_calculated_slots, npc_total_slots, slots):
        """ Adds a non capped slot for the npc and gender """
        rounded_value = npc_total_slots - int(npc_total_slots)
        self.npcs_rounded_results[gender][npc] = rounded_value
        slots.calculated_slots = int(npc_calculated_slots)
        self.npcs_non_capped_results[gender][npc] = slots

    def _add_capped_slot(self, gender, npc, npc_max_slots, npc_world_champion_slots, slots):
        self.npcs_rounded_results[gender].clear()
        self.npcs_non_capped_results[gender].clear()
        slots.calculated_slots = npc_max_slots - npc_world_champion_slots
        slots.capped = True
        self.npcs_capped_results[gender][npc] = slots
        self.event_result_list.remove_entire_npc(npc, gender)
        self._remaining_number_of_slots[gender] -= (npc_max_slots - npc_world_champion_slots)

    def _calculate_npc_by_gender(self, gender):
        swimmers_and_weights = self.event_result_list.get_list_of_swimmers_and_max_weight()
        total_weight = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender])

        npcs = self.event_result_list.get_unique_npcs(gender)
        npc_max_slots = self._npc_max_slots[gender]
        total_slots = self._remaining_number_of_slots[gender]
        wc_results = self._world_champion_event_results

        logging.info("Total slots being assigned: %s" % total_slots)

        if len(npcs) == 0:
            logging.warning("Strange, no NPC found in calculation step")

        for npc in npcs:
            npc_weight_sum = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender and x[0].npc == npc])
            npc_world_champ_slots = sum([1 for x in wc_results if x.swimmer.gender == gender and x.swimmer.npc == npc])
            weight_ratio = npc_weight_sum / total_weight if total_weight > 0 else 0
            npc_calculated_slots = total_slots * weight_ratio
            npc_total_slots = npc_calculated_slots + npc_world_champ_slots

            slots = Slots(npc, gender, weight_percentage=npc_total_slots, wc_slots=npc_world_champ_slots)

            if npc_total_slots <= int(npc_max_slots):
                logging.info("- %s. %d slots (WC:%d, Calculated: %d). Ratio %.4f.",
                             npc, int(npc_total_slots), npc_world_champ_slots, npc_calculated_slots, weight_ratio)

                self._add_non_capped_slot(gender, npc, npc_calculated_slots, npc_total_slots, slots)
            elif npc_total_slots > npc_max_slots:
                logging.info("- %s. %d slots. Ratio %.4f. CAPPED. Should have gotten %d (WC:%d, Calculated: %d) slots without cap", npc,
                             npc_max_slots, weight_ratio, npc_total_slots, npc_world_champ_slots, npc_calculated_slots)
                logging.info("  - All non-capped calculations will be repeated")

                self._add_capped_slot(gender, npc, npc_max_slots, npc_world_champ_slots, slots)
                self._calculate_npc_by_gender(gender)  # Recursive call
                return

        self._add_rounding_slots(gender)

        results = self.npcs_non_capped_results[gender].copy()
        results.update(self.npcs_capped_results[gender])

        self._final_results += ([x[1] for x in results.items()])

    def _add_rounding_slots(self, gender):
        """
        Adds rounding results to the non capped list of results.
        Goes through the rounding list and assigns slots to the npcs with highest rounding values.
        Skips over npcs that already have achieved the capped number of slots
        """
        num_non_capped_slots = sum([result.total_slots() for result in self.npcs_non_capped_results[gender].values()])
        num_capped_slots = sum([capped_res.total_slots() for capped_res in self.npcs_capped_results[gender].values()])
        num_assigned_slots = num_non_capped_slots + num_capped_slots
        num_rounding_slots = self._total_number_of_slots[gender] - num_assigned_slots

        logging.info("Rounding for gender '%s'. num_non_capped_slots:%d. num_capped_slots: %d. num_assigned_slots: %d",
                     gender, num_non_capped_slots, num_capped_slots, num_assigned_slots)
        if num_rounding_slots > 0:
            logging.info("%d places need to be distributed due to rounding", num_rounding_slots)
        elif num_rounding_slots == 0:
            logging.info("No rounding places to distribute")
        elif num_rounding_slots < 0:
            logging.error("Negative rounding value. Something went wrong with the calculations")

        sorted_rounded_npc_list = self._get_sorted_rounded_list(gender)
        for i in range(num_rounding_slots):
            if len(sorted_rounded_npc_list) > 0:
                npc = sorted_rounded_npc_list.pop(0)
                # Skip over npcs that already have maximum number of slots
                while self.npcs_non_capped_results[gender][npc] == self._npc_max_slots[gender]:
                    npc = sorted_rounded_npc_list.pop(0)
                logging.info("%s gets 1 slot for its rounding value %.3f", npc, self.npcs_rounded_results[gender][npc])

                self.npcs_non_capped_results[gender][npc].calculated_slots += 1

    def _get_sorted_rounded_list(self, gender):
        """ Returns a list of npc sorted by the highest rounding values """
        # Convert dict to tuple list, sort tuple list and return list of npcs
        tuple_list = self.npcs_rounded_results[gender].items()
        sorted_tuple_list = sorted(tuple_list, key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_tuple_list]

    def _handle_world_champion_events(self):
        """
        Add 1/2 place finishers to _world_champion_event_results.
        Then nullify their weights so that they don't count in weight calculations
        """
        logging.info(
            "Handle WC event (nullify 1/2 place swimmer weights since they already get slots for that placing)")

        world_champion_results = []

        for world_champion_event_code in self._world_champion_event_codes:
            #event_competitors = self.event_result_list.get_single_event(world_champion_event_code)
            world_champion_results.extend(self.event_result_list.get_single_event(world_champion_event_code))

        # Make sure each swimmer is only counted once
        filtered_for_first_and_second = [x for x in world_champion_results if x.rank <= 2]
        competitor_ids = set([x.swimmer.id for x in filtered_for_first_and_second])
        filtered_for_unique_competitors = []

        for competitor_id in competitor_ids:
            for event_result in filtered_for_first_and_second:
                if event_result.swimmer.id == competitor_id:
                    filtered_for_unique_competitors.append(event_result)
                    break

        self._world_champion_event_results.extend(filtered_for_unique_competitors)

        for wc_result in self._world_champion_event_results:
            self.event_result_list.nullify_swimmer(wc_result.swimmer.id)

    def _attach_minimum_requirements(self):
        """ Attach the minimum requirement list to the event list so that the event list can filter """
        self.event_result_list.attach_minimum_requirements(self.min_requirement_list)

    def _nullify_unqualified_results(self):
        """ Sets weights to 0 for all unqualified results """
        self.event_result_list.nullify_unqualified_results()

    def _initialize_logging(self):
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    def _load_csv_files(self, event_list_csv_list, min_requirement_csv_list, csv_separator):
        """ Load the event list and min requirement files into memory """
        self.event_result_list = EventResultList(event_list_csv_list, csv_separator)
        self.event_result_list.load_csv_file()

        if min_requirement_csv_list:
            self.min_requirement_list = MinimumRequirementList(min_requirement_csv_list, csv_separator)
            self.min_requirement_list.load_csv_file()
            self._attach_minimum_requirements()
            self._nullify_unqualified_results()
        else:
            logging.info("No minimum requirements document found")

    def _initial_data_setup(self, event_list_csv_list, min_requirement_csv_list, csv_separator):
        """ Initializes the csv files, handles the world champion events and calculates remaining slots """
        self._load_csv_files(event_list_csv_list, min_requirement_csv_list, csv_separator)
        self._handle_world_champion_events()

        male_wc_competitors = self._get_number_of_wc_competitors(MALE)
        female_we_competitors = self._get_number_of_wc_competitors(FEMALE)
        logging.info("Removing %d male and %d female world champion slots before calculations."
                     % (male_wc_competitors, female_we_competitors))

        self._remaining_number_of_slots[MALE] = self._total_number_of_slots[MALE] - male_wc_competitors
        self._remaining_number_of_slots[FEMALE] = self._total_number_of_slots[FEMALE] - female_we_competitors

    def _get_number_of_wc_competitors(self, gender):
        world_champion_slots = sum([1 for x in self._world_champion_event_results if x.swimmer.gender == gender])
        return world_champion_slots


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
        logging.info("Nullifying event result lines with times below msq times. This means their weights are set to 0")
        counter = 0
        for result in self.event_results:
            if result.result_time_ms > result.minimum_requirement_time_ms:
                result.weight = 0
                counter += 1
        logging.info("=> %d lines nullified" % counter)

    def get_unique_npcs(self, gender=None):
        return sorted(list(set([x.swimmer.npc for x in self.event_results
                                if x.swimmer.gender == gender or gender is None])))  # Set is used to remove duplicates

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
