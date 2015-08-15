import configparser
from Para_calculations import Logic, MALE, FEMALE


class ConfigFile:
    def __init__(self):
        self.events_file_path = ''
        self.world_champion_event_ids_file_path = ''
        self.minimum_requirements_file_path = ''
        self.npc_max_number_of_males = 0
        self.npc_max_number_of_females = 0
        self.total_number_of_males = 0
        self.total_number_of_females = 0
        self.csv_separator = ""

    def load_config_file(self, config_file_name):
        config = configparser.ConfigParser()
        config.read(config_file_name)

        self.events_file_path = config['FILES']['events_file']
        self.world_champion_event_ids_file_path = config['FILES']['world_champion_event_ids_file']
        self.minimum_requirements_file_path = config['FILES']['minimum_requirements_file']

        self.npc_max_number_of_males = int(config['PARAMETERS']['npc_max_number_of_males'])
        self.npc_max_number_of_females = int(config['PARAMETERS']['npc_max_number_of_females'])
        self.total_number_of_males = int(config['PARAMETERS']['total_number_of_males'])
        self.total_number_of_females = int(config['PARAMETERS']['total_number_of_females'])
        self.csv_separator = config['PARAMETERS']['csv_separator']


def main():
    config_file = ConfigFile()
    config_file.load_config_file('config.ini')

    event_csv_content = []
    world_champion_event_ids = []
    min_requirement_csv_content = []

    with open(config_file.events_file_path) as event_csv_file:
        event_csv_content.extend(event_csv_file.readlines())

    with open(config_file.world_champion_event_ids_file_path) as wc_events_file:
        world_champion_event_ids.extend(wc_events_file.readline().split(','))

    if config_file.minimum_requirements_file_path:
        with open(config_file.minimum_requirements_file_path) as min_req_file:
            min_requirement_csv_content.extend(min_req_file.readlines())

    logic = Logic(event_csv_content,
                  min_requirement_csv_content,
                  world_champion_event_ids,
                  config_file.npc_max_number_of_males,
                  config_file.npc_max_number_of_females,
                  config_file.total_number_of_males,
                  config_file.total_number_of_females,
                  config_file.csv_separator)

    results = logic.calculate_npcs_numbers()

    for result in results:
        print("%s, %s, %d" % (result.npc, result.gender, result.total_slots()))

    male_results = [x for x in results if x.gender == MALE]
    print("Total male slots: ", sum(x.total_slots() for x in male_results))
    female_results = [x for x in results if x.gender == FEMALE]
    print("Total female slots: ", sum(x.total_slots() for x in female_results))


if __name__ == "__main__":
    main()