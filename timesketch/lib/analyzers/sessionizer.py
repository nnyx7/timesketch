"""Sessionizer plugin."""
from __future__ import unicode_literals
import itertools

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

def process_first_event(events):
    try:
        first_event = next(events)
        first_event.add_attributes({'session_number': 1})
        first_event.commit()
        return first_event.source.get('timestamp')
    except StopIteration:
        return None


class SessionizerSketchPlugin(interface.BaseSketchAnalyzer):

    NAME = 'sessionizer'
    max_time_diff = 300000000

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(SessionizerSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = ('*')

        return_fields = ['timestamp']

        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        curr_session_num = 0
  

        # if peeked is not None:
        #     first_event = peeked[0]
        #     last_time_stamp = first_event.source.get('timestamp')
        #     curr_session_num = 1
        #     first_event.add_attributes({'session_number': curr_session_num})
        #     first_event.commit()

        # try:
        #     first_event = next(events)
        #     last_time_stamp = first_event.source.get('timestamp')
        #     curr_session_num = 1
        #     first_event.add_attributes({'session_number': curr_session_num})
        #     first_event.commit()
        # except StopIteration:
        #     continue
        last_time_stamp = process_first_event(events)
        if last_time_stamp is not None:
            curr_session_num = 1
            for event in events:
                curr_time_stamp = event.source.get('timestamp')
                if curr_time_stamp - last_time_stamp > self.max_time_diff:
                    curr_session_num += 1

                event.add_attributes({'session_number': curr_session_num})

                last_time_stamp = curr_time_stamp
                # Commit the event to the datastore.
                event.commit()

            self.sketch.add_view(
                'Session view', 'sessionizer', query_string=query)

        # TODO: Return a summary from the analyzer.
        return ('Sessionizing completed, number of session created: {0:d}'.format(curr_session_num))


manager.AnalysisManager.register_analyzer(SessionizerSketchPlugin)
