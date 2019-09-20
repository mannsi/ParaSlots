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

        self.wc_gender_index = 0
        self.wc_swimmer_id_index = 0
        self.wc_npc_index = 0

        self.ranking_gender_index = 0
        self.ranking_swimmer_id_index = 0
        self.ranking_npc_index = 0
        self.ranking_rank_index = 0
        self.ranking_qualification_index = 0

    def load_config_file(self, config_file_name):
        config = configparser.ConfigParser()
        config.read(config_file_name)

        self.world_champion_results_file = config['FILES']['world_champion_results_file']
        self.rankings_file = config['FILES']['rankings_file']

        self.output_file_name = config['PARAMETERS']['output_file_name']
        self.npc_max_number_of_males = int(config['PARAMETERS']['npc_max_number_of_males'])
        self.npc_max_number_of_females = int(config['PARAMETERS']['npc_max_number_of_females'])
        self.total_number_of_males = int(config['PARAMETERS']['total_number_of_males'])
        self.total_number_of_females = int(config['PARAMETERS']['total_number_of_females'])
        self.csv_separator = config['PARAMETERS']['csv_separator']

        self.wc_gender_index = int(config['PARAMETERS']['wc_file_gender_index'])
        self.wc_swimmer_id_index = int(config['PARAMETERS']['wc_file_swimmer_id_index'])
        self.wc_npc_index = int(config['PARAMETERS']['wc_file_npc_index'])

        self.ranking_gender_index = int(config['PARAMETERS']['ranking_file_gender_index'])
        self.ranking_swimmer_id_index = int(config['PARAMETERS']['ranking_file_swimmer_id_index'])
        self.ranking_npc_index = int(config['PARAMETERS']['ranking_file_npc_index'])
        self.ranking_rank_index = int(config['PARAMETERS']['ranking_file_rank_index'])
        self.ranking_qualification_index = int(config['PARAMETERS']['ranking_file_qualification_index'])


def main():
    config = ConfigFile()
    # TODO take a param that is config name with config2020.ini as default
    # config.load_config_file('files/config2016.ini')
    config.load_config_file('files/config2020.ini')

    logging.basicConfig(filename=config.output_file_name, filemode='w+', format='%(message)s', level=logging.DEBUG)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.info(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))

    rankings_csv_lines = []
    world_champion_lines = []

    with open(config.rankings_file) as rankings_csv_file:
        rankings_csv_lines.extend(rankings_csv_file.readlines())

    with open(config.world_champion_results_file) as world_champion_results_file:
        world_champion_lines.extend(world_champion_results_file.readlines())

    ranking_list = get_ranking_list(rankings_csv_lines,
                                    config.csv_separator,
                                    config.ranking_swimmer_id_index,
                                    config.ranking_gender_index,
                                    config.ranking_npc_index,
                                    config.ranking_rank_index,
                                    config.ranking_qualification_index)

    wc_results = get_world_champion_results(world_champion_lines[1:],
                                            config.csv_separator,
                                            config.wc_swimmer_id_index,
                                            config.wc_gender_index,
                                            config.wc_npc_index)

    logic = Logic(ranking_list,
                  wc_results,
                  config.npc_max_number_of_males,
                  config.npc_max_number_of_females,
                  config.total_number_of_males,
                  config.total_number_of_females)

    results = logic.calculate_npcs_numbers()

    unique_npc = sorted(set([x.npc for x in results]))

    logging.info("")
    logging.info("FINAL RESULTS")
    for npc in unique_npc:
        num_npc_males = sum([x.total_slots() for x in results if x.npc == npc and x.gender == MALE])
        num_npc_females = sum([x.total_slots() for x in results if x.npc == npc and x.gender == FEMALE])
        logging.info("%s: (M: %d, \tF: %d)" % (npc, num_npc_males, num_npc_females))

    logging.info("")

    male_results = [x for x in results if x.gender == MALE]
    logging.info("Total male slots: %d", sum(x.total_slots() for x in male_results))
    female_results = [x for x in results if x.gender == FEMALE]
    logging.info("Total female slots: %d", sum(x.total_slots() for x in female_results))


def get_ranking_list(rankings_lines, separator, swimmer_id_index, gender_index, npc_index, rank_index, ranking_qualification_index):
    rankings_list = RankingsList()
    rankings_list.load_csv_content(rankings_lines, separator, swimmer_id_index, gender_index, npc_index, rank_index,ranking_qualification_index)
    return rankings_list


def get_world_champion_results(world_champion_lines, separator, swimmer_id_index, gender_index, npc_index):
    world_champion_result_list = WorldChampionResultList()
    world_champion_result_list.load_csv_content(world_champion_lines, separator, swimmer_id_index, gender_index, npc_index)
    return world_champion_result_list


if __name__ == "__main__":
    main()
