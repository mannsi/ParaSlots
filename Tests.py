from Para_calculations import *

__author__ = 'mannsi'

import unittest

number_of_event_fields = 15

# TODO need WC test

class TestParaLogic(unittest.TestCase):
    def test_simple_only_males(self):
        """ Single race, only males, everybody should be included """

        ranking_list = RankingsList()
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(10, MALE, "UKR"), True))
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(10, MALE, "UKR"), True))
        ranking_list.add_ranking(Ranking("", "", 2, Swimmer(20, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 3, Swimmer(30, MALE, "GRE"), True))

        logic = Logic(ranking_list, WorldChampionResultList(), npc_max_number_of_males=2,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self.assertEqual(2, len(list_of_npcs_and_swimmers))

    def test_male_and_female(self):
        """ Test when there are both male and female swimmers. Also test if min req time can eliminate a swimmer """

        ranking_list = RankingsList()
        ranking_list.add_ranking(Ranking("", "50m Freestyle S3", 1, Swimmer(10, MALE, "UKR"), True))
        ranking_list.add_ranking(Ranking("", "50m Freestyle S3", 2, Swimmer(20, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "50m Freestyle S3", 3, Swimmer(30, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "50m Freestyle S4", 4, Swimmer(40, FEMALE, "UKR"), True))
        ranking_list.add_ranking(Ranking("", "50m Freestyle S4", 5, Swimmer(50, FEMALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "50m Freestyle S4", 6, Swimmer(60, FEMALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "50m Freestyle S4", 7, Swimmer(70, FEMALE, "ICE"), True))

        logic = Logic(ranking_list, WorldChampionResultList(), npc_max_number_of_males=2,
                      npc_max_number_of_females=2, total_number_of_males=3, total_number_of_females=3)

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('UKR', FEMALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', FEMALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('ICE', FEMALE, 1, list_of_npcs_and_swimmers)
        self.assertEqual(5, len(list_of_npcs_and_swimmers))

    def test_swimmers_with_multiple_results(self):
        """ Swimmers with multiple results should not be counted multiple times. """

        ranking_list = RankingsList()
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(10, MALE, "UKR"), True))
        ranking_list.add_ranking(Ranking("", "", 2, Swimmer(20, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 3, Swimmer(40, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(40, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(40, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(40, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(40, MALE, "GRE"), True))

        logic = Logic(ranking_list, WorldChampionResultList(), npc_max_number_of_males=3,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()

        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self.assertEqual(2, len(list_of_npcs_and_swimmers))

    def test_npc_cap_reached(self):
        """ Test when an npcs should receive more swimmers than the npc cap """

        ranking_list = RankingsList()
        ranking_list.add_ranking(Ranking("", "", 10, Swimmer(40, MALE, "ICE"), True))
        ranking_list.add_ranking(Ranking("", "", 1, Swimmer(10, MALE, "UKR"), True))
        ranking_list.add_ranking(Ranking("", "", 2, Swimmer(20, MALE, "GRE"), True))
        ranking_list.add_ranking(Ranking("", "", 3, Swimmer(30, MALE, "GRE"), True))

        logic = Logic(ranking_list, WorldChampionResultList(), npc_max_number_of_males=1,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()

        self._assert_result_in('GRE', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('ICE', MALE, 1, list_of_npcs_and_swimmers)
        self.assertEqual(3, len(list_of_npcs_and_swimmers))

    def test_rounding_of_seats(self):
        """ Test when there is rounding in the number of seats for swimmers """

        ranking_list = RankingsList()

        for i in range(29):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("A" + str(i), MALE, "A"), True))

        for i in range(20):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("B" + str(i), MALE, "B"), True))

        for i in range(17):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("C" + str(i), MALE, "C"), True))

        for i in range(13):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("D" + str(i), MALE, "D"), True))

        for i in range(9):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("E" + str(i), MALE, "E"), True))

        for i in range(7):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("F" + str(i), MALE, "F"), True))

        for i in range(5):
            ranking_list.add_ranking(Ranking("", "", 1, Swimmer("G" + str(i), MALE, "G"), True))

        logic = Logic(ranking_list, WorldChampionResultList(), npc_max_number_of_males=3,
                      npc_max_number_of_females=0, total_number_of_males=10, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        total_number_of_male_competitors = 0
        for result in list_of_npcs_and_swimmers:
            total_number_of_male_competitors += result.total_slots()

        self.assertEqual(10, total_number_of_male_competitors, msg="10 male swimmers should have been chosen")

        # Before rounding it should be A:2, B:2, C:1, D:1 leaving 4 more swimmers. They should go to the npcs with the
        # highest margin (A, C, E, F) meaning everybody except G should get a swimmer

        self._assert_result_in('A', MALE, 3, list_of_npcs_and_swimmers)
        self._assert_result_in('B', MALE, 2, list_of_npcs_and_swimmers)
        self._assert_result_in('C', MALE, 2, list_of_npcs_and_swimmers)
        self._assert_result_in('D', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('E', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('F', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('G', MALE, 0, list_of_npcs_and_swimmers)

        self.assertEqual(7, len(list_of_npcs_and_swimmers))

    def test_ranking_list(self):
        ranking_list = RankingsList()

        # Empty with header
        logic = Logic(ranking_list, WorldChampionResultList(),
                      npc_max_number_of_males=2, npc_max_number_of_females=0, total_number_of_males=3,
                      total_number_of_females=0)
        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self.assertEqual(0, len(list_of_npcs_and_swimmers))

    def _assert_result_in(self, npc, gender, num_slots, list_of_results):
        self.assertIn((npc, gender, num_slots), [(x.npc, x.gender, x.total_slots()) for x in list_of_results])


if __name__ == '__main__':
    unittest.main()
