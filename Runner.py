import configparser
from Para_calculations import Logic, MALE, FEMALE


class ConfigFile:
    def __init__(self):
        self.rankings_file = ''
        self.world_champion_results_file = ''
        self.minimum_requirements_file_path = ''
        self.npc_max_number_of_males = 0
        self.npc_max_number_of_females = 0
        self.total_number_of_males = 0
        self.total_number_of_females = 0
        self.csv_separator = ""

    def load_config_file(self, config_file_name):
        config = configparser.ConfigParser()
        config.read(config_file_name)

        self.rankings_file = config['FILES']['rankings_file']
        self.world_champion_results_file = config['FILES']['world_champion_results_file']

        self.npc_max_number_of_males = int(config['PARAMETERS']['npc_max_number_of_males'])
        self.npc_max_number_of_females = int(config['PARAMETERS']['npc_max_number_of_females'])
        self.total_number_of_males = int(config['PARAMETERS']['total_number_of_males'])
        self.total_number_of_females = int(config['PARAMETERS']['total_number_of_females'])
        self.csv_separator = config['PARAMETERS']['csv_separator']


def main():
    config_file = ConfigFile()
    config_file.load_config_file('config.ini')

    rankings_csv_content = []
    world_champion_results = []
    min_requirement_csv_content = []

    with open(config_file.rankings_file) as rankings_csv_file:
        rankings_csv_content.extend(rankings_csv_file.readlines())

    with open(config_file.world_champion_results_file) as world_champion_results_file:
        world_champion_results.extend(world_champion_results_file.readline().split(','))

    logic = Logic(rankings_csv_content,
                  min_requirement_csv_content,
                  world_champion_results,
                  config_file.npc_max_number_of_males,
                  config_file.npc_max_number_of_females,
                  config_file.total_number_of_males,
                  config_file.total_number_of_females,
                  config_file.csv_separator)

    results = logic.calculate_npcs_numbers()

    unique_npc = sorted(set([x.npc for x in results]))

    print("")
    print("FINAL RESULTS")
    for npc in unique_npc:
        num_npc_males = sum([x.total_slots() for x in results if x.npc == npc and x.gender == MALE])
        num_npc_females = sum([x.total_slots() for x in results if x.npc == npc and x.gender == FEMALE])
        print("%s: (M: %d, F: %d)" % (npc, num_npc_males, num_npc_females))

    male_results = [x for x in results if x.gender == MALE]
    print("Total male slots: ", sum(x.total_slots() for x in male_results))
    female_results = [x for x in results if x.gender == FEMALE]
    print("Total female slots: ", sum(x.total_slots() for x in female_results))


if __name__ == "__main__":
    main()