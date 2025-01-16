import contextlib
from typing import Optional

import apache_beam as beam
import apache_beam.transforms.error_handling
try:
  from apache_beam.yaml.yaml_errors import map_errors_to_standard_format
except ImportError:
  from apache_beam.yaml.yaml_mapping import _map_errors_to_standard_format as map_errors_to_standard_format

import roman


class ToRomanNumerals(beam.PTransform):
  """A simple transform with external dependencies.
  
  Note that it takes and returns schema'd PCollections.
  """

  def expand(self, pcoll):
    return pcoll | beam.Map(
        lambda row: beam.Row(roman=roman.toRoman(row.value)))


class FromRomanNumerals(beam.PTransform):
  """The inverse of ToRomanNumerals."""

  def __init__(self, error_handling=None):
    self._error_handling = error_handling

  def expand(self, pcoll):
    # Here we conditionally set up a context.
    if self._error_handling is None:
      error_handling_context = contextlib.nullcontext()
    else:
      error_handling_context = beam.transforms.error_handling.CollectingErrorHandler(
      )

    # Run our code, possibly catching errors.
    with error_handling_context as error_handler:
      result = pcoll | beam.Map(
          lambda row: beam.Row(value=roman.fromRoman(row.roman))
      ).with_error_handler(error_handler)

    if self._error_handling is None:
      # If error handling was not requested, return the bare result.
      # Due to the null error handling context above, any errors
      # will be raised and halt the pipeline itself.
      # Alternatively, we could have unconditionally caught the
      # errors and explicitly failed the pipeline if the errors
      # PCollection was non-empty.
      return result
    else:
      # Otherwise return a dict of the result and possibly some errors.
      return {
          'result': result,
          self._error_handling['output']: error_handler.output()
          # These need to be mapped to the schema expected by yaml,
          # which also ensures the errors are serializable.
          | map_errors_to_standard_format(pcoll.element_type)
      }


class StringifyRow(beam.PTransform):
  # The docstring here will become the documentation of the YAML transform,
  # and its args (including their types and descriptions below) are pulled
  # out to construct the configuration schema.
  # When used in a YAML pipeline, the config parameter is passed here as
  # kwargs.
  # We allow None and assign defaults below to indicate that the arguments
  # are actually optional.
  def __init__(
      self,
      item_sep: Optional[str] = None,
      kv_sep: Optional[str] = None,
      prefix: Optional[str] = None,
      suffix: Optional[str] = None):
    """
    Returns a customizable string representation of the each row.
    
    Args:
      item_sep: A string used to separate items in the row, defaults to ', '.
      kv_sep: A string used to join keys and values, defaults to ', '.
      prefix: A string to use as the prefix, defaults to the empty string.
      suffix: A string to use as the suffix, defaults to the empty string.
    """
    self.item_sep = item_sep or ', '
    self.kv_sep = kv_sep or ': '
    self.prefix = prefix or ''
    self.suffix = suffix or ''

  def expand(self, pcoll):
    return pcoll | beam.Map(
        lambda row: beam.Row(
            stringified=self.prefix + self.item_sep.join(
                f'{k}{self.kv_sep}{v}'
                for (k, v) in row._asdict().items()) + self.suffix))


class MultiInputMultiOutput(beam.PTransform):
  """An example transform with multiple inputs and multiple outputs.
  
  This does aggregations and a join via side inputs, taking two inputs
  and returning two outputs.
  
  Taking a single input and returning two outputs, or taking a multiple
  inputs and returning a single output, are handled according to whether
  the input (respectively output) of expand is a dict or a single
  PCollection.
  """

  def expand(self, pcolls):
    # Input pcolls will be a dict
    temp_per_city = pcolls['city_measurements']
    city_to_state_pcoll = pcolls['city_to_state']
    avg_per_city = (
        temp_per_city
        | 'PerCity' >> beam.GroupBy('city').aggregate_field(
            'temperature',
            beam.transforms.combiners.MeanCombineFn(),
            'temperature')
        # This remapping is just so we can compare directly against rows in our
        # tests. Generally any named tuple (such as the one produced by the
        # transform above) that can give us a schema will do.
        | beam.Map(
            lambda result: beam.Row(
                city=result.city, temperature=result.temperature)))
    max_per_state = (
        temp_per_city
        | beam.Map(
            lambda row, city_to_state: beam.Row(
                state=city_to_state[row.city], temperature=row.temperature),
            # Side input.
            city_to_state=beam.pvalue.AsDict(city_to_state_pcoll))
        | 'PerState' >> beam.GroupBy('state').aggregate_field(
            'temperature', max, 'temperature')
        # Likewise.
        | beam.Map(
            lambda result: beam.Row(
                state=result.state, temperature=result.temperature)))
    # As will output pcolls.
    return dict(avg_per_city=avg_per_city, max_per_state=max_per_state)
