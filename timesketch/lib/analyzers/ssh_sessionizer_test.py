"""Tests for SSHSessionizerSketchPlugin"""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers.ssh_sessionizer import SSHSessionizerSketchPlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers.sequence_sessionizer_test \
    import _create_mock_event

# Message attributes for events that represent one mock SSH session.
one_ssh_session_args = [{
    'message':
    '[sshd] [1]: Connection from 1.1.1.1 port 1 on 1.1.1.1 port 1'
}, {
    'message': '[sshd] [1]: Accepted certificate ID'
}]

# Message attributes for events that represent two mock SSH sessions.
many_ssh_session_args = [{
    'message':
    '[sshd] [1]: Connection from 1.1.1.1 port 1 on 1.1.1.1 port 1'
}, {
    'message': '[sshd] [1]: Accepted certificate ID'
}, {
    'message':
    '[sshd] [2]: Connection from 2.2.2.2 port 2 on 2.2.2.2 port 2'
}, {
    'message': '[sshd] [2]: Accepted certificate ID'
}]

# Message attributes for a SSH event that is not a connection SSH event
no_ssh_session_args = [{
    'message': '[sshd] [0]: Loaded keys'
}]


class TestSSHSessionizerPlugin(BaseTest):
    """Tests the functionality of the ssh sessionizing sketch analyzer."""
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_sessionizer(self):
        """Test basic ssh sessionizer functionality."""
        index = 'test_index'
        sketch_id = 1
        sessionizer = SSHSessionizerSketchPlugin(index, sketch_id)
        self.assertIsInstance(sessionizer, SSHSessionizerSketchPlugin)
        self.assertEqual(index, sessionizer.index_name)
        self.assertEqual(sketch_id, sessionizer.sketch.id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_session_starts_with_connection_event(self):
        """Test a session is created if it starts with SSH connection event."""
        index = 'test_index'
        sketch_id = 1
        sessionizer = SSHSessionizerSketchPlugin(index, sketch_id)
        sessionizer.datastore.client = mock.Mock()
        datastore = sessionizer.datastore

        _create_mock_event(datastore, 0, 1, one_ssh_session_args)

        message = sessionizer.run()
        self.assertEqual(
            message,
            'Sessionizing completed, number of {0:s} sessions created: 1'.
            format(sessionizer.session_type))

        session_id = '1.1.1.1_1'
        #pylint: disable=unexpected-keyword-arg
        event = datastore.get_event('test_index', '0', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_all_events_from_session_are_labeled(self):
        """Test one SSH session of events is finded and allocated correctly."""
        index = 'test_index'
        sketch_id = 1
        sessionizer = SSHSessionizerSketchPlugin(index, sketch_id)
        sessionizer.datastore.client = mock.Mock()
        datastore = sessionizer.datastore

        _create_mock_event(datastore, 0, 2, one_ssh_session_args, [1])

        message = sessionizer.run()
        self.assertEqual(
            message,
            'Sessionizing completed, number of {0:s} sessions created: 1'.
            format(sessionizer.session_type))

        session_id = '1.1.1.1_1'
        #pylint: disable=unexpected-keyword-arg
        event = datastore.get_event('test_index', '0', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id)
        event = datastore.get_event('test_index', '101', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_session_doesnt_start_with_no_connection_event(self):
        """Test a session is not created if it doesn't start with SSH connection
        event."""
        index = 'test_index'
        sketch_id = 1
        sessionizer = SSHSessionizerSketchPlugin(index, sketch_id)
        sessionizer.datastore.client = mock.Mock()
        datastore = sessionizer.datastore

        _create_mock_event(datastore, 0, 1, no_ssh_session_args)

        message = sessionizer.run()
        self.assertEqual(
            message,
            'Sessionizing completed, number of {0:s} sessions created: 0'.
            format(sessionizer.session_type))

        #pylint: disable=unexpected-keyword-arg
        event = datastore.get_event('test_index', '0', stored_events=True)
        self.assertNotIn('session_id', event['_source'])


    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_multiple_sessions(self):
        """Test multiple sessions are found and allocated correctly."""
        index = 'test_index'
        sketch_id = 1
        sessionizer = SSHSessionizerSketchPlugin(index, sketch_id)
        sessionizer.datastore.client = mock.Mock()
        datastore = sessionizer.datastore

        _create_mock_event(datastore,
                           0,
                           4,
                           many_ssh_session_args,
                           time_diffs=[1, 1, 1])

        message = sessionizer.run()
        self.assertEqual(
            message,
            'Sessionizing completed, number of {0:s} sessions created: 2'.
            format(sessionizer.session_type))

        session_id_1 = '1.1.1.1_1'
        session_id_2 = '2.2.2.2_2'

        #pylint: disable=unexpected-keyword-arg
        event = datastore.get_event('test_index', '0', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id_1)

        event = datastore.get_event('test_index', '101', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id_1)

        event = datastore.get_event('test_index', '202', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id_2)

        event = datastore.get_event('test_index', '303', stored_events=True)
        self.assertEqual(
            event['_source']['session_id'][sessionizer.session_type],
            session_id_2)
