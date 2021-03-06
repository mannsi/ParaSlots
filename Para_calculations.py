__author__ = 'mannsi'

import datetime
import logging

MALE = "M"
FEMALE = "W"


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
        self._remaining_number_of_non_wc_slots = {MALE: 0, FEMALE: 0}  # Total # of slots - WC slots - capped slots

        male_wc_competitors = self._get_number_of_wc_competitors(MALE)
        female_we_competitors = self._get_number_of_wc_competitors(FEMALE)
        logging.info("")
        logging.info(
            "WORLD CHAMPION SLOTS: %d male and %d female assigned."
            % (male_wc_competitors, female_we_competitors))

        self._remaining_number_of_non_wc_slots[MALE] = self._total_number_of_slots[MALE] - male_wc_competitors
        self._remaining_number_of_non_wc_slots[FEMALE] = self._total_number_of_slots[FEMALE] - female_we_competitors
        self._nullify_world_champion_swimmers()

    def calculate_npcs_numbers(self):
        self._calculate_npc_by_gender(MALE)
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
        self._remaining_number_of_non_wc_slots[gender] -= (npc_max_slots - npc_world_champion_slots)

    def _calculate_npc_by_gender(self, gender, is_recursion=False):
        logging.info("")
        logging.info(f"CALCULATING NPC {'MALE' if gender is MALE else 'FEMALE'} SLOTS {'AGAIN' if is_recursion else ''}")
        swimmers_and_weights = self._ranking_list.get_list_of_swimmers_and_max_weight()
        total_weight = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender])

        npcs = self._ranking_list.get_unique_npcs(gender)
        npc_max_slots = self._npc_max_slots[gender]
        total_calculated_slots = self._remaining_number_of_non_wc_slots[gender]
        wc_results = self._world_champion_result_list.get_results()

        total_slots = total_calculated_slots + self._get_number_of_wc_competitors(gender)
        if not is_recursion:
            logging.info(f"Total slots being assigned: {total_slots} ({total_calculated_slots} via weights and {self._get_number_of_wc_competitors(gender)} via WC qualifications)")
        else:
            logging.info(f"Weight slots being assigned: {total_calculated_slots}")

        logging.info(f"DEBUG: Total weight for calculations is {total_weight:.6f}")

        if len(npcs) == 0:
            logging.warning("Strange, no NPC found in calculation step")

        for npc in npcs:
            npc_weight_sum = sum([x[1] for x in swimmers_and_weights if x[0].gender == gender and x[0].npc == npc])
            npc_world_champ_slots = sum([1 for x in wc_results if x.swimmer.gender == gender and x.swimmer.npc == npc])
            weight_ratio = npc_weight_sum / total_weight if total_weight > 0 else 0
            npc_calculated_slots = total_calculated_slots * weight_ratio
            npc_total_slots = npc_calculated_slots + npc_world_champ_slots

            slots = Slots(npc, gender, weight_percentage=npc_total_slots, wc_slots=npc_world_champ_slots)

            logging.info(
                f"- {npc}. {int(npc_total_slots)} slots\t(WC:{npc_world_champ_slots}, Calculated:{int(npc_calculated_slots)})\tNPC weight: {npc_weight_sum:.1f} \tRatio {weight_ratio:.6f}")

            if npc_total_slots <= int(npc_max_slots):
                self._add_non_capped_slot(gender, npc, npc_calculated_slots, npc_total_slots, slots)
            elif npc_total_slots > npc_max_slots:
                logging.info(f"{npc} exceeds the total maximum slots of {npc_max_slots}!")

                non_wc_slots_for_npc = npc_max_slots - npc_world_champ_slots
                remaining_calculated_slots = total_calculated_slots - non_wc_slots_for_npc

                logging.info(f"{npc} will receive {npc_max_slots} slots and their {non_wc_slots_for_npc} non-WC slots will be removed and the remaining {remaining_calculated_slots} slots redistributed among the rest of the NPCs")

                self._add_capped_slot(gender, npc, npc_max_slots, npc_world_champ_slots, slots)
                self._calculate_npc_by_gender(gender, is_recursion=True)  # Recursive call
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

        num_calculated_slots = sum([result.calculated_slots for result in self._npcs_non_capped_results[gender].values()])
        num_weight_slots = self._remaining_number_of_non_wc_slots[gender]
        num_rounding_slots = num_weight_slots - num_calculated_slots

        logging.info("")
        logging.info(f"ROUNDING {'MALE' if gender is MALE else 'FEMALE'}")

        logging.info(f"{num_calculated_slots} slots assigned from weights out of {num_weight_slots} (excluding capped slots). Remaining {num_rounding_slots} rounds slots go to")

        if num_rounding_slots < 0:
            logging.error("Negative rounding value. Something went wrong with the calculations")

        sorted_rounded_npc_list = self._get_sorted_rounded_list(gender)
        for i in range(num_rounding_slots):
            if len(sorted_rounded_npc_list) > 0:
                npc = sorted_rounded_npc_list.pop(0)
                # Skip over npcs that already have maximum number of slots
                while self._npcs_non_capped_results[gender][npc] == self._npc_max_slots[gender]:
                    npc = sorted_rounded_npc_list.pop(0)
                logging.info("-> %s gets 1 slot for its rounding value %.6f", npc, self._npcs_rounded_results[gender][npc])

                self._npcs_non_capped_results[gender][npc].calculated_slots += 1

        logging.info("NPCs who don't receive a rounding slot")
        for npc in sorted_rounded_npc_list:
            rounding_value = self._npcs_rounded_results[gender][npc]
            logging.info("-> %s - %.6f rounding value", npc, rounding_value)

    def _get_sorted_rounded_list(self, gender):
        """ Returns a list of npc sorted by the highest rounding values """
        # Convert dict to tuple list, sort tuple list and return list of npcs
        tuple_list = self._npcs_rounded_results[gender].items()
        sorted_tuple_list = sorted(tuple_list, key=lambda x: x[1], reverse=True)
        return [x[0] for x in sorted_tuple_list]

    def _get_number_of_wc_competitors(self, gender):
        world_champion_slots = sum(
            [1 for x in self._world_champion_result_list.get_results() if x.swimmer.gender == gender])
        return world_champion_slots

    def _nullify_world_champion_swimmers(self):
        """
        1/2 place from world championship already get spots.
        Those swimmers should not be counted when calculating the rest of the slots
        """
        for wc_result in self._world_champion_result_list.get_results():
            self._ranking_list.nullify_swimmer(wc_result.swimmer.id)


class Swimmer:
    def __init__(self, swimmer_id, gender, npc):
        self.id = swimmer_id
        self.gender = gender
        self.npc = npc


class Ranking:
    def __init__(self,
                 rank,
                 swimmer,
                 qualification):
        self.rank = convert_rank(rank)
        self.swimmer = swimmer
        self.qualification = qualification
        self.weight = self._set_weight(self.rank)

    @staticmethod
    def from_csv_line(line, separator, swimmer_id_index, gender_index, npc_index, rank_index, qualification_index):
        split_line = line.split(separator)

        swimmer_id = split_line[swimmer_id_index].strip()
        if not swimmer_id:
            return None

        swimmer = Swimmer(swimmer_id,
                          gender=split_line[gender_index].strip(),
                          npc=split_line[npc_index].strip())
        rank = split_line[rank_index].strip()
        qualification = split_line[qualification_index].strip()

        return Ranking(rank, swimmer, qualification)

    @staticmethod
    def _set_weight(rank):
        if 1 <= rank <= 8:
            return 1
        elif 9 <= rank <= 12:
            return 0.8
        elif 13 <= rank <= 16:
            return 0.6
        elif 17 <= rank:
            return 0.5


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

    def load_csv_content(self, csv_lines, separator, swimmer_id_index, gender_index, npc_index, rank_index, ranking_qualification_index):
        logging.info("")
        logging.info("Loading ranking lines")
        header_line_found = False

        for line in csv_lines:
            if header_line_found:
                self._add_csv_line(line, separator, swimmer_id_index, gender_index, npc_index, rank_index, ranking_qualification_index)
            elif line.startswith("Event Code"):
                header_line_found = True
        logging.info("=> %d event lines loaded" % len(self._rankings))

    def _add_csv_line(self, line, separator, swimmer_id_index, gender_index, npc_index, rank_index, ranking_qualification_index):
        event_result = Ranking.from_csv_line(line, separator, swimmer_id_index, gender_index, npc_index, rank_index, ranking_qualification_index)
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
    def __init__(self, swimmer):
        self.swimmer = swimmer

    @staticmethod
    def from_csv_line(line, separator, swimmer_id_index, gender_index, npc_index):

        split_line = line.split(separator)

        swimmer_id = split_line[swimmer_id_index].strip()
        if not swimmer_id:
            logging.info("Removing world champion line since it had no swimmer id. Line: %s" % line)
            return None

        gender = MALE if split_line[gender_index].strip().startswith('Me') else FEMALE
        npc = split_line[npc_index].strip()

        swimmer = Swimmer(swimmer_id, gender, npc)

        return WorldChampionResult(swimmer=swimmer)


class WorldChampionResultList:
    def __init__(self):
        self.results = []

    def load_csv_content(self, csv_lines, separator, swimmer_id_index, gender_index, npc_index):
        """ Takes lines from the csv_lines and adds them to the results list, making sure no swimmer is added twice """
        logging.info("")
        logging.info("Loading world champion results lines")
        for line in csv_lines:
            result = WorldChampionResult.from_csv_line(line, separator, swimmer_id_index, gender_index, npc_index)
            if not self._swimmer_already_included_in_list(result.swimmer.id):
                self.results.append(result)

        logging.info("=> %d world champion lines loaded" % len(self.results))

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
