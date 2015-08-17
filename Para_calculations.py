__author__ = 'mannsi'

import datetime
import logging

MALE = "M"
FEMALE = "W"


# TODO fix my misunderstanding of wc event list. FOKK
# TODO all the event code based logic is fucked
# TODO change to file based outputs


def convert_rank(swimmer_rank):
    try:
        return int(swimmer_rank)
    except ValueError:
        # Filter out non numeric characters
        sanitized_list = [x for x in swimmer_rank if x.isdigit()]
        return int(''.join(sanitized_list))




class Logic:
    def __init__(self,
                 ranking_list,
                 world_champion_result_list,
                 npc_max_number_of_males,
                 npc_max_number_of_females,
                 total_number_of_males,
                 total_number_of_females):
        self._world_champion_result_list = world_champion_result_list
        self._ranking_list = ranking_list

        self._npc_max_slots = {MALE: npc_max_number_of_males, FEMALE: npc_max_number_of_females}
        self._total_number_of_slots = {MALE: total_number_of_males, FEMALE: total_number_of_females}

        # Holds all npc swimmers who exceeded the max number of slots
        self._npcs_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: Slots}}

        self._npcs_non_capped_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: Slots}}

        # Holds extra rounding values when npcs are assigned swimmers. Used when all
        # npcs have gotten their slots but due to rounding some slots remain.
        self._npcs_rounded_results = {MALE: {}, FEMALE: {}}  # {gender: {npc: rounded_value}}

        self._final_results = []  # list of Slot objects
        self._remaining_number_of_slots = {MALE: 0, FEMALE: 0}  # Total # of slots - WC slots - capped slots

        male_wc_competitors = self._get_number_of_wc_competitors(MALE)
        female_we_competitors = self._get_number_of_wc_competitors(FEMALE)
        logging.info("Removing %d male and %d female world champion slots before calculations."
                     % (male_wc_competitors, female_we_competitors))

        self._remaining_number_of_slots[MALE] = self._total_number_of_slots[MALE] - male_wc_competitors
        self._remaining_number_of_slots[FEMALE] = self._total_number_of_slots[FEMALE] - female_we_competitors

        self._nullify_world_champion_swimmers()

    def calculate_npcs_numbers(self):
        logging.info("CALCULATING NPC MALE SLOTS")
        self._calculate_npc_by_gender(MALE)

        logging.info("CALCULATING NPC FEMALE SLOTS")
        self._calculate_npc_by_gender(FEMALE)
        return self._final_results

    def _add_non_capped_slot(self, gender, npc, npc_calculated_slots, npc_total_slots, slots):
        """ Adds a non capped slot for the npc and gender """
        rounded_value = npc_total_slots - int(npc_total_slots)
        self._npcs_rounded_results[gender][npc] = rounded_value
        slots.calculated_slots = int(npc_calculated_slots)
        self._npcs_non_capped_results[gender][npc] = slots

    def _add_capped_slot(self, gender, npc, npc_max_slots, npc_world_champion_slots, slots):
        self._npcs_rounded_results[gender].clear()
        self._npcs_non_capped_results[gender].clear()
        slots.calculated_slots = npc_max_slots - npc_world_champion_slots
        slots.capped = True
        self._npcs_capped_results[gender][npc] = slots
        self._ranking_list.remove_entire_npc(npc, gender)
        self._remaining_number_of_slots[gender] -= (npc_max_slots - npc_world_champion_slots)

    def _calculate_npc_by_gender(self, gender):
        swimmers_and_weights = self._ranking_list.get_list_of_swimmers_and_max_weight()
        total_weight = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender])

        npcs = self._ranking_list.get_unique_npcs(gender)
        npc_max_slots = self._npc_max_slots[gender]
        total_slots = self._remaining_number_of_slots[gender]
        wc_results = self._world_champion_result_list.get_results()

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
                logging.info("- %s. %d slots (WC:%d, Calculated: %d). Ratio %.4f. Total weight: %.4f",
                             npc, int(npc_total_slots), npc_world_champ_slots, npc_calculated_slots, weight_ratio, total_weight)

                self._add_non_capped_slot(gender, npc, npc_calculated_slots, npc_total_slots, slots)
            elif npc_total_slots > npc_max_slots:
                logging.info(
                    "- %s. %d slots. Ratio %.4f. Total weight: %.4f. CAPPED. Should have gotten %d (WC:%d, Calculated: %d)  without cap",
                    npc,
                    npc_max_slots, weight_ratio, total_weight, npc_total_slots, npc_world_champ_slots, npc_calculated_slots)
                logging.info("  - All non-capped calculations will be repeated")

                self._add_capped_slot(gender, npc, npc_max_slots, npc_world_champ_slots, slots)
                self._calculate_npc_by_gender(gender)  # Recursive call
                return

        self._add_rounding_slots(gender)

        results = self._npcs_non_capped_results[gender].copy()
        results.update(self._npcs_capped_results[gender])

        self._final_results += ([x[1] for x in results.items()])

    def _add_rounding_slots(self, gender):
        """
        Adds rounding results to the non capped list of results.
        Goes through the rounding list and assigns slots to the npcs with highest rounding values.
        Skips over npcs that already have achieved the capped number of slots
        """
        num_non_capped_slots = sum([result.total_slots() for result in self._npcs_non_capped_results[gender].values()])
        num_capped_slots = sum([capped_res.total_slots() for capped_res in self._npcs_capped_results[gender].values()])
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
                while self._npcs_non_capped_results[gender][npc] == self._npc_max_slots[gender]:
                    npc = sorted_rounded_npc_list.pop(0)
                logging.info("%s gets 1 slot for its rounding value %.3f", npc, self._npcs_rounded_results[gender][npc])

                self._npcs_non_capped_results[gender][npc].calculated_slots += 1

        logging.info("NPCs who don't receive a rounding slot (in order)")
        for npc in sorted_rounded_npc_list:
            rounding_value = self._npcs_rounded_results[gender][npc]
            logging.info("-> %s - %.3f rounding value", npc, rounding_value)

    def _get_sorted_rounded_list(self, gender):
        """ Returns a list of npc sorted by the highest rounding values """
        # Convert dict to tuple list, sort tuple list and return list of npcs
        tuple_list = self._npcs_rounded_results[gender].items()
        sorted_tuple_list = sorted(tuple_list, key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_tuple_list]

    def _get_number_of_wc_competitors(self, gender):
        world_champion_slots = sum([1 for x in self._world_champion_result_list.get_results() if x.swimmer.gender == gender])
        return world_champion_slots

    def _nullify_world_champion_swimmers(self):
        """
        1/2 place from world championship already get spots.
        Those swimmers should not be counted when calculating the rest of the slots
        """
        for wc_result in self._world_champion_result_list.get_results():
            self._ranking_list.nullify_swimmer(wc_result.swimmer.id)


class Swimmer:
    def __init__(self, swimmer_id, gender, npc, family_name=None, given_name=None, birth_year=None):
        self.id = swimmer_id
        self.family_name = family_name
        self.given_name = given_name
        self.gender = gender
        self.birth_year = birth_year
        self.npc = npc


class Ranking:
    def __init__(self,
                 event_code,
                 event,
                 swimmer_rank,
                 swimmer,
                 qualification,
                 result_time=0,
                 event_date=None,
                 event_city=None,
                 event_country=None):
        self.event_code = event_code
        self.event = event
        self.rank = convert_rank(swimmer_rank)
        self.swimmer = swimmer
        self.result_time = result_time
        self.result_time_ms = self._time_to_ms(result_time)
        self.event_date = event_date
        self.event_city = event_city
        self.event_country = event_country
        self.minimum_requirement_time = datetime.timedelta()
        self.qualification = qualification
        self.weight = 0

        self._set_weight()

    @staticmethod
    def from_csv_line(line, separator):
        split_line = line.split(separator)

        if len(split_line) != 15:
            raise Exception("Illegal ranking csv line: '" + line + "'")

        swimmer_id = split_line[4].strip()
        if not swimmer_id:
            return None

        swimmer = Swimmer(swimmer_id,
                          family_name=split_line[5].strip(),
                          given_name=split_line[6].strip(),
                          gender=split_line[1].strip(),
                          birth_year=split_line[8].strip(),
                          npc=split_line[7].strip())

        return Ranking(
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


class RankingsList:
    def __init__(self):
        self._rankings = []

    def remove_entire_npc(self, npc, gender):
        others = [x for x in self._rankings if x.swimmer.npc != npc or x.swimmer.gender != gender]
        self._rankings = others

    def get_list_of_swimmers_and_max_weight(self):
        """
        Return a list of swimmers and their maximum weight as tuples
        """
        dict_of_swimmers_and_weight = {}
        for event_result in self._rankings:
            if event_result.swimmer.id not in dict_of_swimmers_and_weight:
                dict_of_swimmers_and_weight[event_result.swimmer.id] = (event_result.swimmer, event_result.weight)
            else:
                previous_swimmer_max_weight = dict_of_swimmers_and_weight.get(event_result.swimmer.id)[1]
                swimmer_max_weight = max(event_result.weight, previous_swimmer_max_weight)
                dict_of_swimmers_and_weight[event_result.swimmer.id] = (event_result.swimmer, swimmer_max_weight)

        return dict_of_swimmers_and_weight.values()

    def load_csv_content(self, csv_lines, separator):
        logging.info("Loading event lines")
        header_line_found = False

        for line in csv_lines:
            if header_line_found:
                self._add_csv_line(line, separator)
            elif line.startswith("Event Code%sGender" % csv_lines):
                header_line_found = True
        logging.info("=> %d event lines loaded" % len(self._rankings))

    def _add_csv_line(self, line, separator):
        event_result = Ranking.from_csv_line(line, separator)
        if not event_result or not event_result.swimmer.id:
            return
        if event_result.qualification in ("MQS", ""):
            self._rankings.append(event_result)

    def get_unique_npcs(self, gender=None):
        return sorted(list(set([x.swimmer.npc for x in self._rankings
                                if x.swimmer.gender == gender or gender is None])))  # Set is used to remove duplicates

    def nullify_swimmer(self, swimmer_id):
        for result in self._rankings:
            if result.swimmer.id == swimmer_id:
                result.weight = 0

    def add_ranking(self, ranking):
        self._rankings.append(ranking)


class WorldChampionResult:
    def __init__(self,
                 swimmer,
                 event,
                 event_code,
                 rank):
        self.swimmer = swimmer
        self.event = event
        self.event_code = event_code
        self.rank = rank

    @staticmethod
    def from_csv_line(line, separator):
        split_line = line.split(separator)

        if len(split_line) != 7:
            raise Exception("Illegal world champion csv line: '%s'" % line)

        swimmer_id = split_line[5].strip()
        if not swimmer_id:
            logging.info("Removing world champion line since it had no swimmer id. Line: %s" % line)
            return None

        swimmer = Swimmer(swimmer_id,
                          family_name=split_line[2].strip(),
                          given_name=split_line[3].strip(),
                          gender="",
                          birth_year="",
                          npc=split_line[1].strip())

        return WorldChampionResult(
            event_code=split_line[6].strip(),
            swimmer=swimmer,
            event=convert_rank(split_line[1].strip()),
            rank=split_line[2].strip()
        )


class WorldChampionResultList:
    def __init__(self):
        self.results = []

    def load_csv_content(self, csv_lines, csv_separator):
        """ Takes lines from the csv_lines and adds them to the results list, making sure no swimmer is added twice """
        for line in csv_lines:
            result = WorldChampionResult.from_csv_line(line, csv_separator)
            if not self._swimmer_already_included_in_list(result.swimmer.id):
                self.results.append(result)

        logging.info("%d world champion lines loaded" % len(csv_lines))

    def get_results(self):
        return self.results

    def _swimmer_already_included_in_list(self, swimmer_id):
        return len([x for x in self.results if x.swimmer.id == swimmer_id]) > 0


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
