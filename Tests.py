from Para_calculations import Logic, MALE, FEMALE

__author__ = 'mannsi'

import unittest
import datetime

number_of_event_fields = 15
event_list_csv_header = \
    "Event Code,Gender,Event,Rank,SDMS ID,Family Name,Given Name,NPC,Birth,Result,Time (ms),Date,City,Country"

class TestParaLogic(unittest.TestCase):
    def test_simple_only_males(self):
        """ Single race, only males, everybody should be included """
        event_list_csv = [event_list_csv_header,
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="2", sdms="20", npc="GRE",
                                                  time="00:29.33", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="3", sdms="30", npc="GRE",
                                                  time="00:30.18", qualified=True)]

        logic = Logic(event_list_csv, world_champion_event_code=[], npc_max_number_of_males=2,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0,
                      csv_separator=',')

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self.assertEqual(2, len(list_of_npcs_and_swimmers))

    def test_male_and_female(self):
        """ Test when there are both male and female swimmers. Also test if min req time can eliminate a swimmer """
        event_list_csv = [event_list_csv_header,
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="2", sdms="20", npc="GRE",
                                                  time="00:29.33", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="3", sdms="30", npc="GRE",
                                                  time="00:30.18", qualified=True),
                          self._create_event_line("E1", FEMALE, "50m Freestyle S4", rank="4", sdms="40", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", FEMALE, "50m Freestyle S4", rank="5", sdms="50", npc="GRE",
                                                  time="00:29.33", qualified=True),
                          self._create_event_line("E1", FEMALE, "50m Freestyle S4", rank="6", sdms="60", npc="GRE",
                                                  time="02:30.00", qualified=False),
                          self._create_event_line("E1", FEMALE, "50m Freestyle S4", rank="7", sdms="70", npc="ICE",
                                                  time="01:00.00", qualified=True)]

        logic = Logic(event_list_csv, world_champion_event_code=[], npc_max_number_of_males=2,
                      npc_max_number_of_females=2, total_number_of_males=3, total_number_of_females=3,
                      csv_separator=',')

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('UKR', FEMALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', FEMALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('ICE', FEMALE, 1, list_of_npcs_and_swimmers)
        self.assertEqual(5, len(list_of_npcs_and_swimmers))

    def test_swimmers_with_multiple_results(self):
        """ Swimmers with multiple results should not be counted multiple times. """

        event_list_csv = [event_list_csv_header,
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="2", sdms="20", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="3", sdms="40", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E2", MALE, "50m Freestyle S3", rank="1", sdms="40", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E3", MALE, "50m Freestyle S3", rank="1", sdms="40", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E4", MALE, "50m Freestyle S3", rank="1", sdms="40", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E5", MALE, "50m Freestyle S3", rank="1", sdms="40", npc="GRE",
                                                  time="00:06.10", qualified=True)]

        logic = Logic(event_list_csv, world_champion_event_code=[], npc_max_number_of_males=3,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0,
                      csv_separator=',')

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()

        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self.assertEqual(2, len(list_of_npcs_and_swimmers))

    def test_world_champion_event_removed(self):
        """ Test removing world champion event """

        event_list_csv = [event_list_csv_header,
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="2", sdms="20", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="3", sdms="30", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E2", MALE, "50m Freestyle S3", rank="1", sdms="40", npc="ASD",
                                                  time="01:06.10", qualified=True),
                          self._create_event_line("E2", MALE, "50m Freestyle S3", rank="2", sdms="50", npc="JKL",
                                                  time="02:06.10", qualified=False),
                          self._create_event_line("E2", MALE, "50m Freestyle S3", rank="3", sdms="60", npc="QWE",
                                                  time="03:06.10", qualified=False)]

        logic = Logic(event_list_csv, world_champion_event_code=['E2'],
                      npc_max_number_of_males=100, npc_max_number_of_females=0, total_number_of_males=5,
                      total_number_of_females=0, csv_separator=',')

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self._assert_result_in('ASD', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('JKL', MALE, 1, list_of_npcs_and_swimmers)

    def test_npc_cap_reached(self):
        """ Test when an npcs should receive more swimmers than the npc cap """

        event_list_csv = [event_list_csv_header,
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="20", sdms="40", npc="ICE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="2", sdms="20", npc="GRE",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="3", sdms="30", npc="GRE",
                                                  time="00:06.10", qualified=True)]

        logic = Logic(event_list_csv, world_champion_event_code=[], npc_max_number_of_males=1,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0,
                      csv_separator=',')

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()

        self._assert_result_in('GRE', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('ICE', MALE, 1, list_of_npcs_and_swimmers)
        self.assertEqual(3, len(list_of_npcs_and_swimmers))

    def test_rounding_of_seats(self):
        """ Test when there is rounding in the number of seats for swimmers """
        event_list_csv = [event_list_csv_header]

        for i in range(29):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="A" + str(i), npc="A", time="00:06.10",
                                                          qualified=True))

        for i in range(20):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="B" + str(i), npc="B", time="00:06.10",
                                                          qualified=True))

        for i in range(17):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="C" + str(i), npc="C", time="00:06.10",
                                                          qualified=True))

        for i in range(13):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="D" + str(i), npc="D", time="00:06.10",
                                                          qualified=True))

        for i in range(9):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="E" + str(i), npc="E", time="00:06.10",
                                                          qualified=True))

        for i in range(7):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="F" + str(i), npc="F", time="00:06.10",
                                                          qualified=True))

        for i in range(5):
            event_list_csv.append(self._create_event_line("E1", MALE, "50m Freestyle S3",
                                                          rank="1", sdms="G" + str(i), npc="G", time="00:06.10",
                                                          qualified=True))

        logic = Logic(event_list_csv, world_champion_event_code=[], npc_max_number_of_males=3,
                      npc_max_number_of_females=0, total_number_of_males=10, total_number_of_females=0,
                      csv_separator=',')

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

    def test_empty_event_files(self):
        """ Testing empty event files with and without header """
        event_list_csv_with_header = [event_list_csv_header]
        event_list_csv_without_header = []

        # Empty with header
        logic = Logic(event_list_csv_with_header, world_champion_event_code=[],
                      npc_max_number_of_males=2, npc_max_number_of_females=0, total_number_of_males=3,
                      total_number_of_females=0, csv_separator=',')
        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self.assertEqual(0, len(list_of_npcs_and_swimmers))

        # Empty without header
        logic = Logic(event_list_csv_without_header, world_champion_event_code=[],
                      npc_max_number_of_males=2, npc_max_number_of_females=0, total_number_of_males=3,
                      total_number_of_females=0, csv_separator=',')
        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self.assertEqual(0, len(list_of_npcs_and_swimmers))

    def test_empty_event_line(self):
        """ Simple test with an added empty event line. It should not change anything """
        event_list_csv = [event_list_csv_header,
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="1", sdms="10", npc="UKR",
                                                  time="00:06.10", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="2", sdms="20", npc="GRE",
                                                  time="00:29.33", qualified=True),
                          self._create_event_line("E1", MALE, "50m Freestyle S3", rank="3", sdms="30", npc="GRE",
                                                  time="00:30.18", qualified=True),
                          (number_of_event_fields - 1) * ","]

        logic = Logic(event_list_csv, world_champion_event_code=[], npc_max_number_of_males=2,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0,
                      csv_separator=',')

        list_of_npcs_and_swimmers = logic.calculate_npcs_numbers()
        self._assert_result_in('UKR', MALE, 1, list_of_npcs_and_swimmers)
        self._assert_result_in('GRE', MALE, 2, list_of_npcs_and_swimmers)
        self.assertEqual(2, len(list_of_npcs_and_swimmers))


    def _create_simple_event_line(self, sdms, gender, npc, time):
        return self._create_event_line("SWMF5001010000", gender, "50m Freestyle S3", "1", sdms, npc, time)

    def _create_event_line(self, event_id, gender, event, rank, sdms, npc, time, qualified):
        qualification_string = ",MQS" if qualified else ",MET"
        return event_id + "," + gender + "," + event + "," + rank + "," \
               + sdms + ",Name1, Name2," + npc + ",1999," + time + "," + str(self._time_to_ms(time)) \
               + qualification_string + ",2015-05-16,Athens,Greece"

    def _time_to_ms(self, time_string):
        (mins, secs, ms) = time_string.replace(".", ":").split(":")
        return int(
            datetime.timedelta(minutes=int(mins), seconds=int(secs), milliseconds=int(ms)).total_seconds() * 1000)

    def _assert_result_in(self, npc, gender, num_slots, list_of_results):
        self.assertIn((npc, gender, num_slots), [(x.npc, x.gender, x.total_slots()) for x in list_of_results])


if __name__ == '__main__':
    unittest.main()
