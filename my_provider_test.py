import unittest

import apache_beam as beam
from apache_beam.testing.util import assert_that
from apache_beam.testing.util import equal_to

import my_provider


class TestTransforms(unittest.TestCase):

  def test_to_roman(self):
    with beam.Pipeline() as p:
      pcoll = p | beam.Create([
          beam.Row(value=1),
          beam.Row(value=99),
          beam.Row(value=2024),
      ])
      result = pcoll | my_provider.ToRomanNumerals()
      assert_that(
          result,
          equal_to([
              beam.Row(roman='I'),
              beam.Row(roman='XCIX'),
              beam.Row(roman='MMXXIV'),
          ]))

  def test_from_roman(self):
    with beam.Pipeline() as p:
      pcoll = p | beam.Create([
          beam.Row(roman='I'),
          beam.Row(roman='XCIX'),
          beam.Row(roman='MMXXIV'),
      ])
      result = pcoll | my_provider.FromRomanNumerals()
      assert_that(
          result,
          equal_to([
              beam.Row(value=1),
              beam.Row(value=99),
              beam.Row(value=2024),
          ]))

  def test_from_roman_with_errors(self):
    with self.assertRaisesRegex(Exception, 'Invalid Roman numeral'):
      with beam.Pipeline() as p:
        pcoll = p | beam.Create([
            beam.Row(roman='I'),
            beam.Row(roman='XCIX'),
            beam.Row(roman='abc'),
        ])
        _ = pcoll | my_provider.FromRomanNumerals()

  def test_from_roman_with_error_handling(self):
    with beam.Pipeline() as p:
      pcoll = p | beam.Create([
          beam.Row(roman='I'),
          beam.Row(roman='XCIX'),
          beam.Row(roman='abc'),
      ])
      results = pcoll | my_provider.FromRomanNumerals(
          error_handling={'output': 'errors'})
      assert_that(
          results['result'],
          equal_to([
              beam.Row(value=1),
              beam.Row(value=99),
          ]))
      assert_that(
          results['errors'] | beam.Map(lambda x: x.element.roman),
          equal_to(['abc']))

  def test_multi_input_multi_output(self):
    with beam.Pipeline() as p:
      city_measurements = p | 'city_measurements' >> beam.Create([
          beam.Row(city='Seattle', temperature=51, date='2024-12-01'),
          beam.Row(city='Seattle', temperature=51, date='2024-12-02'),
          beam.Row(city='Seattle', temperature=45, date='2024-12-03'),
          beam.Row(city='Kirkland', temperature=52, date='2024-12-03'),
          beam.Row(city='New York City', temperature=41, date='2024-12-01'),
          beam.Row(city='New York City', temperature=43, date='2024-12-02'),
      ])
      city_to_state = p | 'city_to_state' >> beam.Create([
          beam.Row(city='Seattle', state='WA'),
          beam.Row(city='Kirkland', state='WA'),
          beam.Row(city='New York City', state='NY'),
      ])
      result = {
          'city_measurements': city_measurements,
          'city_to_state': city_to_state
      } | my_provider.MultiInputMultiOutput()

      assert_that(
          result['avg_per_city'],
          equal_to([
              beam.Row(city='Seattle', temperature=49),
              beam.Row(city='Kirkland', temperature=52),
              beam.Row(city='New York City', temperature=42),
          ]))

      assert_that(
          result['max_per_state'],
          equal_to([
              beam.Row(state='WA', temperature=52),
              beam.Row(state='NY', temperature=43),
          ]))
