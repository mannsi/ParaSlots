from Para_calculations import Logic, MALE, FEMALE

__author__ = 'mannsi'

import unittest
import datetime
#from Para_calculations import *


event_list_csv_header = "Event Code,Gender,Event,Rank,SDMS ID,Family Name,Given Name,NPC,Birth,Result,Time (ms),Date,City,Country"
min_requirement_csv_header = "Event,Gender,MQS /n"


class TestParaLogic(unittest.TestCase):
    def test_simple_only_males(self):
        """ Single race, only males, everybody should be included """
        min_requirement_csv = min_requirement_csv_header + "50m Freestyle S3,MALE,01:00.00"
        event_list_csv = event_list_csv_header \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="10", npc="UKR", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="2", event="50m Freestyle S3", sdms="20", npc="GRE", time="00:29.33") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="3", event="50m Freestyle S3", sdms="30", npc="GRE", time="00:30.18")

        logic = Logic(event_list_csv, min_requirement_csv, world_champion_event_id=None, npc_max_number_of_males=2,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npc_numbers()
        self.assertIn(('UKR', (1, 0)), list_of_npcs_and_swimmers, msg="Ukraine should have a single male swimmer")
        self.assertIn(('GRE', (2, 0)), list_of_npcs_and_swimmers, msg="Greece should have two male swimmers")
        self.assertCountEqual(2, list_of_npcs_and_swimmers, msg="Only 2 npcs should be in list")

    def test_male_and_female(self):
        """ Test when there are both male and female swimmers. Also test if min req time can eliminate a swimmer """
        min_requirement_csv = min_requirement_csv_header + """50m Freestyle S3,MALE,01:00.00
                                 50m Freestyle S4,FEMALE,01:59.50"""

        event_list_csv = event_list_csv_header \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="10", npc="UKR", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="2", event="50m Freestyle S3", sdms="20", npc="GRE", time="00:29.33") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="3", event="50m Freestyle S3", sdms="30", npc="GRE", time="00:30.18") \
            + "/n" + self._create_event_line(event_id="E1", gender=FEMALE, rank="4", event="50m Freestyle S4", sdms="40", npc="UKR", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=FEMALE, rank="5", event="50m Freestyle S4", sdms="50", npc="GRE", time="00:29.33") \
            + "/n" + self._create_event_line(event_id="E1", gender=FEMALE, rank="6", event="50m Freestyle S4", sdms="60", npc="GRE", time="01:30.00") \
            + "/n" + self._create_event_line(event_id="E1", gender=FEMALE, rank="7", event="50m Freestyle S4", sdms="70", npc="ICE", time="02:00.00") # This one should be eliminated

        logic = Logic(event_list_csv, min_requirement_csv, world_champion_event_id=None, npc_max_number_of_males=2,
                      npc_max_number_of_females=2, total_number_of_males=3, total_number_of_females=3)

        list_of_npcs_and_swimmers = logic.calculate_npc_numbers()
        self.assertIn(('UKR', (1, 1)), list_of_npcs_and_swimmers, msg="Ukraine should have a male and female swimmers")
        self.assertIn(('GRE', (2, 1)), list_of_npcs_and_swimmers, msg="Greece should have two male and one female")
        self.assertIn(('ICE', (0, 1)), list_of_npcs_and_swimmers, msg="Iceland should have a single female")

        self.assertCountEqual(3, list_of_npcs_and_swimmers, msg="Only 3 npcs should be in list")

    def test_swimmers_with_multiple_results(self):
        """ Swimmers with multiple results should not be counted multiple times. """
        min_requirement_csv = min_requirement_csv_header + "50m Freestyle S3,MALE,01:00.00"

        event_list_csv = event_list_csv_header \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="10", npc="UKR", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="2", event="50m Freestyle S3", sdms="20", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="3", event="50m Freestyle S3", sdms="40", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E2", gender=MALE, rank="1", event="50m Freestyle S3", sdms="40", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E3", gender=MALE, rank="1", event="50m Freestyle S3", sdms="40", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E4", gender=MALE, rank="1", event="50m Freestyle S3", sdms="40", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E5", gender=MALE, rank="1", event="50m Freestyle S3", sdms="40", npc="GRE", time="00:06.10") \

        logic = Logic(event_list_csv, min_requirement_csv, world_champion_event_id=None, npc_max_number_of_males=3,
                      npc_max_number_of_females=0, total_number_of_males=5, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npc_numbers()
        self.assertIn(('UKR', (1, 0)), list_of_npcs_and_swimmers, msg="Ukraine should have a single male swimmer")
        self.assertIn(('GRE', (2, 0)), list_of_npcs_and_swimmers, msg="Greece should have two male swimmers")
        self.assertCountEqual(2, list_of_npcs_and_swimmers, msg="Only 2 npcs should be in list")

    def test_world_champion_event_removed(self):
        """ Test removing world champion event """
        min_requirement_csv = min_requirement_csv_header + "50m Freestyle S3,MALE,01:00.00"

        event_list_csv = event_list_csv_header \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="10", npc="UKR", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="2", event="50m Freestyle S3", sdms="20", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="3", event="50m Freestyle S3", sdms="30", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E2", gender=MALE, rank="1", event="50m Freestyle S3", sdms="40", npc="ASD", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E2", gender=MALE, rank="2", event="50m Freestyle S3", sdms="50", npc="JKL", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E2", gender=MALE, rank="3", event="50m Freestyle S3", sdms="60", npc="QWE", time="00:06.10")

        logic = Logic(event_list_csv, min_requirement_csv, world_champion_event_id='SWMF5001010001',
                      npc_max_number_of_males=100, npc_max_number_of_females=0, total_number_of_males=100,
                      total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npc_numbers()
        self.assertIn(('UKR', (1, 0)), list_of_npcs_and_swimmers, msg="Ukraine should have a single male swimmer")
        self.assertIn(('GRE', (2, 0)), list_of_npcs_and_swimmers, msg="Greece should have two male swimmers")
        self.assertIn(('ASD', (1, 0)), list_of_npcs_and_swimmers, msg="ASD should place from WC 1st")
        self.assertIn(('JKL', (1, 0)), list_of_npcs_and_swimmers, msg="JKL should place from WC 2nd")
        self.assertNotIn(('QWE', (1, 0)), list_of_npcs_and_swimmers, msg="3rd place on WC is not enough")
        self.assertCountEqual(2, list_of_npcs_and_swimmers, msg="Only 2 npcs should be in list")

    def test_npc_cap_reached(self):
        """ Test when an npcs should receive more swimmers than the npc cap """
        min_requirement_csv = min_requirement_csv_header + "50m Freestyle S3,MALE,01:00.00"

        event_list_csv = event_list_csv_header \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="10", npc="UKR", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="2", event="50m Freestyle S3", sdms="20", npc="GRE", time="00:06.10") \
            + "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="3", event="50m Freestyle S3", sdms="30", npc="GRE", time="00:06.10")

        logic = Logic(event_list_csv, min_requirement_csv, world_champion_event_id=None, npc_max_number_of_males=1,
                      npc_max_number_of_females=0, total_number_of_males=3, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npc_numbers()
        self.assertIn(('UKR', (1, 0)), list_of_npcs_and_swimmers, msg="Ukraine should have a single male swimmer")
        self.assertIn(('GRE', (1, 0)), list_of_npcs_and_swimmers, msg="Greece should only have one male swimmer")
        self.assertCountEqual(2, list_of_npcs_and_swimmers, msg="Only 2 npcs should be in list")

    def test_rounding_of_seats(self):
        """ Test when there is rounding in the number of seats for swimmers """
        min_requirement_csv = min_requirement_csv_header + "50m Freestyle S3,MALE,01:00.00"
        event_list_csv = event_list_csv_header

        for i in range(29):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="A" + str(i), npc="A", time="00:06.10")

        for i in range(20):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="B" + str(i), npc="B", time="00:06.10")

        for i in range(17):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="C" + str(i), npc="C", time="00:06.10")

        for i in range(13):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="D" + str(i), npc="D", time="00:06.10")

        for i in range(9):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="E" + str(i), npc="E", time="00:06.10")

        for i in range(7):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="F" + str(i), npc="F", time="00:06.10")

        for i in range(5):
            event_list_csv += "/n" + self._create_event_line(event_id="E1", gender=MALE, rank="1", event="50m Freestyle S3", sdms="G" + str(i), npc="G", time="00:06.10")

        logic = Logic(event_list_csv, min_requirement_csv, world_champion_event_id=None, npc_max_number_of_males=3,
                      npc_max_number_of_females=0, total_number_of_males=10, total_number_of_females=0)

        list_of_npcs_and_swimmers = logic.calculate_npc_numbers()

        total_number_of_male_competitors = 0
        for result in list_of_npcs_and_swimmers:
            total_number_of_male_competitors += result[1][0]

        self.assertEqual(10, total_number_of_male_competitors, msg="10 male swimmers should have been chosen")

        # Before rounding it should be A:2, B:2, C:1, D:1 leaving 4 more swimmers. They should go to the npcs with the
        # highest margin (A, C, E, F) meaning everybody except G should get a swimmer
        self.assertCountEqual(6, list_of_npcs_and_swimmers, msg="Every npc except 'G' should have gotten swimmers")

        self.assertIn(('A', (3, 0)), list_of_npcs_and_swimmers)
        self.assertIn(('B', (2, 0)), list_of_npcs_and_swimmers)
        self.assertIn(('C', (2, 0)), list_of_npcs_and_swimmers)
        self.assertIn(('D', (1, 0)), list_of_npcs_and_swimmers)
        self.assertIn(('E', (1, 0)), list_of_npcs_and_swimmers)
        self.assertIn(('F', (1, 0)), list_of_npcs_and_swimmers)

    def _create_simple_event_line(self, sdms, gender, npc, time):
        return self._create_event_line("SWMF5001010000", gender, "50m Freestyle S3", "1", sdms, npc, time)

    def _create_event_line(self, event_id, gender, event, rank, sdms, npc, time):
        return event_id + "," + gender + "," + event + "," + rank + "," + sdms + ",Name1, Name2," + npc + ",1999," + time + "," + str(
            self._time_to_ms(time)) + ",2015-05-16,Athens,Greece"

    def _time_to_ms(self, time_string):
        (mins, secs, ms) = time_string.replace(".", ":").split(":")
        return int(
            datetime.timedelta(minutes=int(mins), seconds=int(secs), milliseconds=int(ms)).total_seconds() * 1000)