"""Sketch analyzer plugin for screenshot."""
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class ScreenshotSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Screenshot."""

    NAME = 'screenshot'

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(ScreenshotSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = ('(data_type:"selinux:line" '
                'AND audit_type:"EXECVE" '
                'AND body:"screenshot") '
                'OR (url:"screenshot") '
                'OR (data_type:"fs:stat" '
                'AND filename:"screenshot" '
                'AND timestamp_desc:"Creation Time" '
                'AND file_entry_type:"file")')


        # TODO: Specify what returned fields you need for your analyzer.
        return_fields = ['message', 'data_type', 'source_short']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # TODO: If an emoji is needed fetch it here.
        # my_emoji = emojis.get_emoji('emoji_name')

        # TODO: Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # sketch.add_view(name, query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event_add_label('label')
        # event.add_star()
        # event.add_comment('comment')
        # event.add_emojis([my_emoji])
        # event.add_human_readable('human readable text', self.NAME)

        screenshot_count = 0

        # Get the Unicode for each emoji.
        locomotive = emojis.get_emoji('locomotive')
        trashcan = emojis.get_emoji('wastebasket')
        camera = emojis.get_emoji('camera')
        satellite = emojis.get_emoji('satellite')    
        
        for event in events:
            # Fields to analyze.
            data_type = event.source.get('data_type')
            source_short = event.source.get('source_short')
            message = event.source.get('message')

            # Container for emojis.
            add_emojis = []

            if data_type == 'fs:stat' and 'Trash' in message:
                add_emojis.append(trashcan)
                event.add_tags(['trash'])
                event.add_comment('Screenshot moved to trash.')

            if data_type == 'selinux:line' and 'EXECVE' in message:
                event.add_star()
                add_emojis.append(locomotive)
                # Add new message field to be displayed in the UI.
                event.add_human_readable('Screenshot taken', self.NAME)
                screenshot_count += 1

            if 'screenshot' in message.lower():
                add_emojis.append(camera)

            if source_short == 'WEBHIST':
                add_emojis.append(satellite)
            if add_emojis:
                event.add_emojis(add_emojis)

            # Commit the event to the datastore.
            event.commit()


        if screenshot_count:
            self.sketch.add_view('Screenshot activity', 'screenshot', query_string=query)


        # TODO: Return a summary from the analyzer.
        return ('Screenshot analyzer completed, {0:d} screenshot{1:s} marked'.format(screenshot_count, 's' if screenshot_count > 1 else ''))



manager.AnalysisManager.register_analyzer(ScreenshotSketchPlugin)
