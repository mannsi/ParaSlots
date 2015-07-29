__author__ = 'mannsi'

import datetime


class Logic():
    def __init__(self,
                 event_list_csv,
                 min_requirement_csv,
                 world_champion_event_id,
                 npc_max_number_of_males,
                 npc_max_number_of_females,
                 total_number_of_males,
                 total_number_of_females):
        self.world_champion_event_id = world_champion_event_id
        self.npc_max_number_of_males = npc_max_number_of_males
        self.npc_max_number_of_females = npc_max_number_of_females
        self.total_number_of_males = total_number_of_males
        self.total_number_of_females = total_number_of_females

        self.event_result_list = EventResultList(event_list_csv)
        self.min_requirement_list = MinimumRequirementList(min_requirement_csv)

        self._clean_csv_files()
        self._load_csv_files()
        self._attach_minimum_requirements()
        self._remove_unqualified_results()

    def calculate_npc_numbers(self):
        return []

    def _clean_csv_files(self):
        # TODO
        # This will be implemented once the real csv files are provided.
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
                 event_class,
                 swimmer_rank,
                 swimmer,
                 result_time,
                 event_date,
                 event_city,
                 event_country):
        self.event_code = event_code
        self.event = event
        self.event_class = event_class
        self.swimmer_rank = swimmer_rank
        self.swimmer = swimmer
        self.result_time = result_time
        self.result_time_ms = self._time_to_ms(result_time)
        self.event_date = event_date
        self.event_city = event_city
        self.event_country = event_country
        self.minimum_requirement_time = datetime.timedelta()
        self.minimum_requirement_time_ms = 0

        self._set_weight()

    def set_min_requirement_time(self, min_requirement_time):
        self.minimum_requirement_time = min_requirement_time
        self.minimum_requirement_time_ms = EventResult._time_to_ms(min_requirement_time)

    def _set_weight(self):
        if 1 <= self.swimmer_rank <= 8:
            self.weight = 1
        elif 9 <= self.swimmer_rank <= 12:
            self.weight = 0.8
        elif 13 <= self.swimmer_rank <= 16:
            self.weight = 0.6
        elif 17 <= self.swimmer_rank:
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

    def load_csv_file(self):
        header_line_found = False

        for line in self.csv_file_content:
            if header_line_found:
                self._add_csv_line(line)
            elif line.startswith("Event Code, Gender"):
                header_line_found = True

    def _add_csv_line(self, line):
        split_line = line.split(',')

        if len(split_line) != 14:
            raise Exception("Illegal event result csv line: '" + line + "'")

        swimmer = Swimmer(swimmer_id=split_line[4],
                          family_name=split_line[5],
                          given_name=split_line[6],
                          gender=split_line[1],
                          birth_year=split_line[8],
                          npc=split_line[7])

        event_result = EventResult(
            event_code=split_line[0],
            swimmer=swimmer,
            event=split_line[2],
            swimmer_rank=split_line[3],
            result_time=split_line[9],
            event_date=split_line[11],
            event_city=split_line[12],
            event_country=split_line[13]
        )
        self.event_results.append(event_result)

    def attach_minimum_requirements(self, minimum_requirement_list):
        for event_result in self.event_results:
            min_requirement = minimum_requirement_list.get_min_requirement(event_result.event)
            event_result.set_min_requirement_time(min_requirement.mqs)

    def remove_unqualified_results(self):
        self.event_results = [x for x in self.event_results if x.result_time_ms < x.minimum_requirement_time_ms]


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

        for line in self.csv_file_content:
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

        min_requirement = MinimumRequirement(event=split_line[0],
                                             gender=split_line[1],
                                             mqs=split_line[2])
        self.min_requirements.append(min_requirement)
