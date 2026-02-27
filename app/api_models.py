from flask_restx import fields
from flask_restx import Namespace

# Create namespace instances that will be imported by route modules
entries_ns = Namespace('entries', description='Calendar entries operations')
categories_ns = Namespace('categories', description='Category management operations')
quotes_ns = Namespace('quotes', description='Quote management operations')
grafana_ns = Namespace('grafana', description='Grafana integration endpoints')
maintenance_ns = Namespace('maintenance', description='Maintenance and administration operations')
giphy_ns = Namespace('giphy', description='Giphy integration endpoints')

# Common models
error_model = entries_ns.model('Error', {
    'error': fields.String(required=True, description='Error message')
})

success_model = entries_ns.model('Success', {
    'message': fields.String(required=True, description='Success message')
})

# Category models
category_model = categories_ns.model('Category', {
    'id': fields.Integer(description='Category ID'),
    'name': fields.String(required=True, description='Category name'),
    'symbol': fields.String(description='Category symbol/emoji'),
    'color_hex': fields.String(description='Category color in hex format'),
    'repeat_annually': fields.Boolean(description='Whether category repeats annually'),
    'display_celebration': fields.Boolean(description='Whether to display celebration animation'),
    'is_protected': fields.Boolean(description='Whether category is protected from deletion'),
    'last_updated_by': fields.String(description='IP address of last updater')
})

category_input_model = categories_ns.model('CategoryInput', {
    'name': fields.String(required=True, description='Category name'),
    'symbol': fields.String(description='Category symbol/emoji'),
    'color_hex': fields.String(description='Category color in hex format'),
    'repeat_annually': fields.Boolean(description='Whether category repeats annually'),
    'display_celebration': fields.Boolean(description='Whether to display celebration animation'),
    'is_protected': fields.Boolean(description='Whether category is protected from deletion')
})

# Entry models
entry_model = entries_ns.model('Entry', {
    'id': fields.Integer(description='Entry ID'),
    'date': fields.String(required=True, description='Entry date in YYYY-MM-DD format'),
    'title': fields.String(required=True, description='Entry title'),
    'description': fields.String(description='Entry description'),
    'url': fields.String(description='Associated URL'),
    'image_filename': fields.String(description='Image filename if any'),
    'cancelled': fields.Boolean(description='Whether entry is cancelled'),
    'category_id': fields.Integer(required=True, description='Category ID'),
    'category': fields.Nested(category_model, description='Category details'),
    'last_updated_by': fields.String(description='IP address of last updater')
})

entry_input_model = entries_ns.model('EntryInput', {
    'date': fields.String(required=True, description='Entry date in YYYY-MM-DD format'),
    'title': fields.String(required=True, description='Entry title'),
    'description': fields.String(description='Entry description'),
    'url': fields.String(description='Associated URL'),
    'category': fields.String(required=True, description='Category name')
})

# Quote models
quote_model = quotes_ns.model('Quote', {
    'id': fields.Integer(description='Quote ID'),
    'text': fields.String(required=True, description='Quote content (supports Markdown)'),
    'author': fields.String(required=True, description='Quote author'),
    'category': fields.String(description='Quote category'),
    'url': fields.String(description='Reference URL'),
    'last_shown': fields.DateTime(description='Last time quote was shown'),
    'last_updated_by': fields.String(description='IP address of last updater')
})

quote_input_model = quotes_ns.model('QuoteInput', {
    'text': fields.String(required=True, description='Quote content (supports Markdown, max 1000 chars)'),
    'author': fields.String(required=True, description='Quote author (max 200 chars)'),
    'category': fields.String(description='Quote category (max 100 chars)'),
    'url': fields.String(description='Reference URL (max 500 chars)')
})

quote_response_model = quotes_ns.model('QuoteResponse', {
    'text': fields.String(description='Quote content (HTML formatted)'),
    'author': fields.String(description='Quote author'),
    'category': fields.String(description='Quote category'),
    'url': fields.String(description='Reference URL'),
    'period': fields.String(description='Quote period (Daily/Random)'),
    'background_color': fields.String(description='Generated background color')
})

# API Data models
api_data_model = entries_ns.model('ApiData', {
    'entries': fields.List(fields.Nested(entry_model), description='List of entries'),
    'categories': fields.List(fields.Nested(category_model), description='List of categories')
})

# Grafana models
grafana_target_model = grafana_ns.model('GrafanaTarget', {
    'target': fields.String(required=True, description='Target category name'),
    'type': fields.String(required=True, description='Query type (timeserie)')
})

grafana_query_request_model = grafana_ns.model('GrafanaQueryRequest', {
    'targets': fields.List(fields.Nested(grafana_target_model), required=True, description='List of targets'),
    'range': fields.Raw(description='Time range (optional)')
})

grafana_datapoint_model = grafana_ns.model('GrafanaDatapoint', {
    'target': fields.String(description='Target category name'),
    'datapoints': fields.List(fields.List(fields.Raw), description='Data points [value, timestamp]')
})

grafana_annotation_request_model = grafana_ns.model('GrafanaAnnotationRequest', {
    'annotation': fields.Raw(required=True, description='Annotation query object')
})

grafana_annotation_model = grafana_ns.model('GrafanaAnnotation', {
    'annotation': fields.Raw(description='Original annotation query'),
    'time': fields.Integer(description='Timestamp in milliseconds'),
    'title': fields.String(description='Annotation title'),
    'tags': fields.List(fields.String, description='Tags'),
    'text': fields.String(description='Annotation text')
})

grafana_tag_key_model = grafana_ns.model('GrafanaTagKey', {
    'type': fields.String(description='Tag type'),
    'text': fields.String(description='Tag key name')
})

grafana_tag_value_request_model = grafana_ns.model('GrafanaTagValueRequest', {
    'key': fields.String(required=True, description='Tag key to get values for')
})

grafana_tag_value_model = grafana_ns.model('GrafanaTagValue', {
    'text': fields.String(description='Tag value')
})

# Giphy models
giphy_search_response_model = giphy_ns.model('GiphySearchResponse', {
    'data': fields.List(fields.Raw, description='Array of GIF data from Giphy API')
})

giphy_url_response_model = giphy_ns.model('GiphyUrlResponse', {
    'url': fields.String(description='Full Giphy API request URL')
})

giphy_enabled_response_model = giphy_ns.model('GiphyEnabledResponse', {
    'enabled': fields.Boolean(description='Whether Giphy integration is enabled')
})

# Maintenance models
batch_import_model = maintenance_ns.model('BatchImportData', {
    'categories': fields.List(fields.Nested(category_input_model), description='Categories to import'),
    'entries': fields.List(fields.Raw, description='Entries to import'),
    'quotes': fields.List(fields.Nested(quote_input_model), description='Quotes to import')
})
