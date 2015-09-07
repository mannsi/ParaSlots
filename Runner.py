import configparser
import logging
from datetime import datetime

from Para_calculations import Logic, RankingsList, WorldChampionResultList, MALE, FEMALE


class ConfigFile:
    def __init__(self):
        self.rankings_file = ''
        self.world_champion_results_file = ''
        self.npc_max_number_of_males = 0
        self.npc_max_number_of_females = 0
        self.total_number_of_males = 0
        self.total_number_of_females = 0
        self.csv_separator = ""
        self.output_file_name = ""
        self.name_of_run = ""
        self.number_of_decimals = 0

    def load_config_file(self, config_file_name):
        config = configparser.ConfigParser()
        config.read(config_file_name)

        self.world_champion_results_file = config['FILES']['world_champion_results_file']
        self.rankings_file = config['FILES']['rankings_file']

        self.output_file_name = config['PARAMETERS']['output_file_name']
        self.name_of_run = config['PARAMETERS']['name_of_run']
        self.npc_max_number_of_males = int(config['PARAMETERS']['npc_max_number_of_males'])
        self.npc_max_number_of_females = int(config['PARAMETERS']['npc_max_number_of_females'])
        self.total_number_of_males = int(config['PARAMETERS']['total_number_of_males'])
        self.total_number_of_females = int(config['PARAMETERS']['total_number_of_females'])
        self.csv_separator = config['PARAMETERS']['csv_separator']
        self.number_of_decimals = config['PARAMETERS']['number_of_decimals']


def main():
    config_file = ConfigFile()
    config_file.load_config_file('config.ini')

    logging.basicConfig(filename=config_file.output_file_name, filemode='w', format='%(message)s', level=logging.DEBUG)
    logging.info(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
    logging.info("== %s ==", config_file.name_of_run)

    rankings_csv_lines = []
    world_champion_lines = []

    with open(config_file.rankings_file) as rankings_csv_file:
        rankings_csv_lines.extend(rankings_csv_file.readlines())

    with open(config_file.world_champion_results_file) as world_champion_results_file:
        world_champion_lines.extend(world_champion_results_file.readlines())

    logic = Logic(get_ranking_list(rankings_csv_lines, config_file.csv_separator),
                  get_world_champion_results(world_champion_lines[1:], config_file.csv_separator),
                  config_file.npc_max_number_of_males,
                  config_file.npc_max_number_of_females,
                  config_file.total_number_of_males,
                  config_file.total_number_of_females,
                  config_file.number_of_decimals)

    results = logic.calculate_npcs_numbers()

    unique_npc = sorted(set([x.npc for x in results]))

    logging.info("")
    logging.info("FINAL RESULTS")
    for npc in unique_npc:
        num_npc_males = sum([x.total_slots() for x in results if x.npc == npc and x.gender == MALE])
        num_npc_females = sum([x.total_slots() for x in results if x.npc == npc and x.gender == FEMALE])
        logging.info("%s: (M: %d,\tF: %d)" % (npc, num_npc_males, num_npc_females))

    logging.info("")

    male_results = [x for x in results if x.gender == MALE]
    logging.info("Total male slots: %d", sum(x.total_slots() for x in male_results))
    female_results = [x for x in results if x.gender == FEMALE]
    logging.info("Total female slots: %d", sum(x.total_slots() for x in female_results))


def get_ranking_list(rankings_lines, csv_separator):
    rankings_list = RankingsList()
    rankings_list.load_csv_content(rankings_lines, csv_separator)
    return rankings_list


def get_world_champion_results(world_champion_lines, csv_separator):
    world_champion_result_list = WorldChampionResultList()
    world_champion_result_list.load_csv_content(world_champion_lines, csv_separator)
    return world_champion_result_list

if __name__ == "__main__":
    main()
