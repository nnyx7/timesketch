"""Tests for ScreenshotPlugin."""
from __future__ import unicode_literals

import unittest
import mock
import copy

from timesketch.lib.analyzers import sessionizer
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers.interface import Event
from timesketch.models.user import User
from timesketch.models.sketch import Sketch

class TestSessionizerPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestSessionizerPlugin, self).__init__(*args, **kwargs)

    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_analyzer(self):
        """Test basic analyzer functionality."""
        index = 'test_index'
        sketch_id = 1
        analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
        self.assertIsInstance(analyser, SessionizerSketchPlugin)
        self.assertEqual(index, analyser.index_name)
        self.assertEqual(sketch_id, analyser.sketch.id)

    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_same_session(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[200], quantity=2)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 1')
            
            ds = MockDataStore("test", 0)
            event1 = (ds.get_event('test_index', '0', store_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '1', store_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)

    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_diff_session(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[400000000], quantity=2)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 2')
            
            ds = MockDataStore("test", 0)
            event1 = (ds.get_event('test_index', '0', store_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '1', store_events=True))
            self.assertEqual(event2['_source']['session_number'], 2)
            
    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_multiple_sessions(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[300000000, 400000000], quantity=3)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 2')
            
            ds = MockDataStore("test", 0)
            event1 = (ds.get_event('test_index', '0', store_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '1', store_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)
            event3 = (ds.get_event('test_index', '2', store_events=True))
            self.assertEqual(event3['_source']['session_number'], 2)

    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_edge_time_diff(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[300000000], quantity=2)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 1')
            
            ds = MockDataStore("test", 0)
            event1 = (ds.get_event('test_index', '0', store_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '1', store_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)


    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_zero_time_diff(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[0], quantity=2)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 1')
            
            ds = MockDataStore("test", 0)
            event1 = (ds.get_event('test_index', '0', store_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            event2 = (ds.get_event('test_index', '1', store_events=True))
            self.assertEqual(event2['_source']['session_number'], 1)


    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_zero_events(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[], quantity=0)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 0')

    @mock.patch(
        u'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_one_event(self):
        with mock.patch.object(SessionizerSketchPlugin, 'event_stream', return_value=_create_mock_event(0, time_diffs=[], quantity=1)):
            index = 'test_index'
            sketch_id = 1
            analyser = sessionizer.SessionizerSketchPlugin(index, sketch_id)
            message = analyser.run()
            self.assertEqual(message, 'Sessionizing completed, number of session created: 1')
            ds = MockDataStore("test", 0)
            event1 = (ds.get_event('test_index', '0', store_events=True))
            self.assertEqual(event1['_source']['session_number'], 1)
            

def _create_mock_event(event_id, attrs=None, time_diffs=None, quantity=None):
    """
    Returns an instance of Event, based on the MockDataStore event_dict
    example, updated with the attributes specified.
    """
    ts = 1410895419859714
    event_template = {
            '_index': [],
            '_id': str(event_id),
            '_type': 'plaso_event',
            '_source': {
                'es_index': '',
                'es_id': '',
                'label': '',
                'timestamp': ts,
                'timestamp_desc': '',
                'datetime': '2014-09-16T19:23:40+00:00',
                'source_short': '',
                'source_long': '',
                'message': '',
            }
        }

    ds = MockDataStore("test", 0)
    user = User('test_user')
    sketch = Sketch('test_sketch', 'description', user)
    label = sketch.Label(label='Test label', user=user)
    sketch.labels.append(label)

    if not time_diffs:
        time_diffs = [0]
    if quantity is None:
        quantity = 1

    events = []

    if (quantity - len(time_diffs) > 0):
        time_diffs.extend([time_diffs[len(time_diffs) - 1]] * (quantity - len(time_diffs)))

    for i in range(quantity):
        event = event_template
        event['_id'] = str(event_id)
        event['_source']['timestamp'] = ts
        event_id += 1
        ts += time_diffs[i]
        eventObj = Event(copy.deepcopy(event), ds, sketch)
        events.append(eventObj)
        ds.import_event(eventObj.index_name, eventObj.event_type,
                        event_id=eventObj.event_id, event=eventObj.source)
    

    for e in events:
        yield e


if __name__ == '__main__':
    unittest.main()